extends RefCounted
## Svet tvrze vymodelovany v Blenderu (blender/export_game.py): nacte modely/tvrz.glb,
## priradi materialy podle jmen, postavi kolize, rostliny (MultiMesh po bunkach) a predá
## informace o ohnich, mistnostech a pouzitelnych vecech hernimu zivotu (life.gd).

const MOD := "res://modely/"
const BUNKA := 24.0
## textury s vyskovou mapou -> parallax (hloubka v metrech)
const HLOUBKA := {"dlazba": 0.04, "dlazba_hrad": 0.035, "kocicky": 0.05, "piskovec": 0.02, "podlaha": 0.008, "prkna_ven": 0.012, "sindel": 0.035, "skala_piskovec": 0.07, "kamen": 0.04, "kamen_lisejnik": 0.05}

var info: Dictionary
var data: Dictionary
var sum: NoiseTexture2D
var _tex := {}
var _mats := {}
var water_y := -2.75
var water_mat: ShaderMaterial          # hladina prikopu (kruhove vlnky)
## rostliny ke sberu: druh rostliny ve svete -> predmet v brasne; kazda instance je sberne misto (sber.gd)
const SBER := {"nettle_plant": "kopriva", "celandine_01": "vlastovicnik", "periwinkle_plant": "barvinek"}
var grass_mesh: Mesh                   # trs travy (3 karty) i pro travu v krajine (trava.gd)
var sber_spots: Array = []             # {"id", "mmi", "i", "xf"}
var vodni: Array = []                  # materialy vody (vlnky a ceřeni od hrace nastavuje voda.gd)
const VRSTVA_VODA := 1 << 19           # plochy hladin jako Area3D (zjisteni, ze hrac stoji ve vode)


func _init(p_info: Dictionary) -> void:
	info = p_info


func build(parent: Node3D, quality: int) -> void:
	var f := FileAccess.open(MOD + "svet.json", FileAccess.READ)
	data = JSON.parse_string(f.get_as_text())
	water_y = float(data.get("voda_y", -2.75))
	_make_noise()
	var scene: PackedScene = load(MOD + "tvrz.glb")
	var root := scene.instantiate()
	root.name = "Tvrz"
	parent.add_child(root)
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		_apply_materials(mi)
		# oboustranne stiny: tenke vrstvy (omitka uvnitr, prkna) jinak propousteji svetlo ve skvirach
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		var nm := String(mi.name)
		if nm.begins_with("Teren") or nm.begins_with("Nadvori"):
			_trimesh(mi)
		if nm.begins_with("Teren"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # rozpocet: velky teren nekreslit do stinu
		if nm.begins_with("Rakos") or nm.begins_with("Slama"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_end = 70.0
	_collisions(parent)
	_static_items(parent)
	_info()
	_plants(parent, quality)
	_ves_grass(parent, quality)


# ------------------------------------------------------------------ materialy

func _make_noise() -> void:
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = 0.012
	fn.fractal_octaves = 5
	sum = NoiseTexture2D.new()
	sum.width = 512
	sum.height = 512
	sum.seamless = true
	sum.noise = fn
	sum.generate_mipmaps = true


func _t(name: String, kind: String) -> Texture2D:
	var key := "%s_%s" % [name, kind]
	if not _tex.has(key):
		_tex[key] = load(MOD + "textury/%s.jpg" % key)
	return _tex[key]


func _size(name: String) -> float:
	var s: Array = data["textury"].get(name, [2.0, 2.0])
	return float(s[0])


func material(name: String) -> Material:
	var base := name.split(".")[0]
	if _mats.has(base):
		return _mats[base]
	var d: Dictionary = data["materialy"].get(base, {})
	var m: Material
	match String(d.get("type", "")):
		"zdivo":
			var s := ShaderMaterial.new()
			s.shader = load("res://shaders/zdivo.gdshader")
			var om: String = d["omitka"]
			s.set_shader_parameter("kamen_a", _t("zdivo", "diff"))
			s.set_shader_parameter("kamen_n", _t("zdivo", "nor"))
			s.set_shader_parameter("kamen_r", _t("zdivo", "rough"))
			s.set_shader_parameter("kamen_h", _t("zdivo", "disp"))
			s.set_shader_parameter("omitka_a", _t(om, "diff"))
			s.set_shader_parameter("omitka_n", _t(om, "nor"))
			s.set_shader_parameter("omitka_r", _t(om, "rough"))
			s.set_shader_parameter("kamen_m", _size("zdivo"))
			s.set_shader_parameter("omitka_m", _size(om))
			s.set_shader_parameter("kryti", float(d["kryti"]))
			s.set_shader_parameter("tint", _v3(d["tint"]))
			s.set_shader_parameter("kamen_tint", _v3(d["kamen"]))
			s.set_shader_parameter("spina", float(d["spina"]))
			s.set_shader_parameter("sum", sum)
			m = s
		"tex":
			var s2 := ShaderMaterial.new()
			s2.shader = load("res://shaders/textura.gdshader")
			var tx: String = d["tex"]
			s2.set_shader_parameter("tex_a", _t(tx, "diff"))
			s2.set_shader_parameter("tex_n", _t(tx, "nor"))
			s2.set_shader_parameter("tex_r", _t(tx, "rough"))
			s2.set_shader_parameter("velikost", _size(tx))
			s2.set_shader_parameter("prohodit", bool(d["swap"]))
			s2.set_shader_parameter("svet", String(d["coord"]) == "world")
			s2.set_shader_parameter("tint", _v3(d["tint"]))
			s2.set_shader_parameter("sedost", float(d.get("grey", 0.0)))
			if d.has("tint2"):
				s2.set_shader_parameter("tint2", _v3(d["tint2"]))
				s2.set_shader_parameter("pestrost", 1.0)
			if tx in ["skala_piskovec", "kamen_lisejnik", "kamen"]:
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("antitile", 1.0)
				s2.set_shader_parameter("skvrny", 1.0)
			if tx == "sindel":
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("skvrny", 1.0)
				s2.set_shader_parameter("radky", 1.0)
			if tx in ["tram", "prkna_ven", "okenice", "omitka_bila", "malta", "dosky", "drevo_stare", "kura"] and String(base) not in ["dub", "deska", "prkna"]:
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("stekance", 0.55 if String(base).begins_with("roubeni") or String(base) in ["lata", "dub_ven", "sindel_hra"] else 0.4)
				s2.set_shader_parameter("skvrny", 0.6)
			if bool(d["swap"]) and String(d["coord"]) == "uv":
				s2.set_shader_parameter("kus", 1.0)
			if HLOUBKA.has(tx) and (String(d["coord"]) == "world" or tx in ["sindel", "skala_piskovec"]):
				s2.set_shader_parameter("tex_h", _t(tx, "disp"))
				s2.set_shader_parameter("hloubka", HLOUBKA[tx])
			m = s2
		"zem":
			var s3 := ShaderMaterial.new()
			s3.shader = load("res://shaders/zem.gdshader")
			s3.set_shader_parameter("hlina_a", _t("hlina", "diff"))
			s3.set_shader_parameter("hlina_n", _t("hlina", "nor"))
			s3.set_shader_parameter("trava_a", _t("trava", "diff"))
			s3.set_shader_parameter("trava_n", _t("trava", "nor"))
			s3.set_shader_parameter("hlina_m", _size("hlina"))
			s3.set_shader_parameter("sum", sum)
			m = s3
		"rybnik":
			# rybnik (okrehek, mirne kalny) a potok (tekouci, cisty - dno videt)
			var s4 := ShaderMaterial.new()
			s4.shader = load("res://shaders/voda.gdshader")
			s4.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
			s4.set_shader_parameter("sum", sum)
			var tek := float(d.get("tekouci", 0.0))
			s4.set_shader_parameter("tekouci", tek)
			s4.set_shader_parameter("okrehek", 0.0 if tek > 0.5 else 1.0)
			s4.set_shader_parameter("kalnost", 0.35 if tek > 0.5 else 0.7)
			s4.set_shader_parameter("zakal", Color(0.1, 0.11, 0.07) if tek > 0.5 else Color(0.07, 0.09, 0.04))
			vodni.append(s4)
			m = s4
		"malba":
			var s5 := ShaderMaterial.new()
			s5.shader = load("res://shaders/malba.gdshader")
			s5.set_shader_parameter("zaklad", _v3(d["zaklad"]))
			s5.set_shader_parameter("barva", _v3(d["barva"]))
			s5.set_shader_parameter("sum", sum)
			m = s5
		"sklo":
			var s6 := ShaderMaterial.new()
			s6.shader = load("res://shaders/sklo.gdshader")
			s6.set_shader_parameter("terce", bool(d.get("terce", false)))
			m = s6
		"trava":
			var g := StandardMaterial3D.new()
			g.albedo_color = Color(_v3(d["col"]).x, _v3(d["col"]).y, _v3(d["col"]).z)
			g.vertex_color_use_as_albedo = false
			g.cull_mode = BaseMaterial3D.CULL_DISABLED
			g.roughness = 0.75
			g.backlight_enabled = true
			g.backlight = Color(0.25, 0.3, 0.1)
			m = g
		"voda":
			# prikop: stejna hladina jako rybnik (posouvane vlnky) a kruhove vlnky z life.gd
			var w := ShaderMaterial.new()
			w.shader = load("res://shaders/voda.gdshader")
			w.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
			w.set_shader_parameter("sum", sum)
			w.set_shader_parameter("deep", Color(0.03, 0.045, 0.035))
			w.set_shader_parameter("kalnost", 0.82)
			vodni.append(w)
			water_mat = w
			m = w
		_:
			var sm := StandardMaterial3D.new()
			var c: Array = d.get("col", [0.5, 0.48, 0.45])
			sm.albedo_color = Color(c[0], c[1], c[2])
			sm.roughness = float(d.get("rough", 0.8))
			sm.metallic = float(d.get("metal", 0.0))
			if d.has("emit"):
				sm.emission_enabled = true
				sm.emission = Color(c[0], c[1], c[2])
				sm.emission_energy_multiplier = minf(float(d["emit"]), 4.0)
			m = sm
	_mats[base] = m
	return m


func _v3(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _apply_materials(mi: MeshInstance3D) -> void:
	var mesh := mi.mesh
	if mesh == null:
		return
	for i in mesh.get_surface_count():
		var old := mesh.surface_get_material(i)
		var nm := old.resource_name if old else ""
		if nm != "":
			var mt := material(nm)
			mi.set_surface_override_material(i, mt)
			if vodni.has(mt):
				_hladina(mi, i)


## Hladina jako oblast (jen pro dotaz "je tu voda a v jake vysce"), ne kolize; male nadoby vynechat.
func _hladina(mi: MeshInstance3D, i: int) -> void:
	var arr := mi.mesh.surface_get_arrays(i)
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var bb := am.get_aabb()
	if maxf(bb.size.x, bb.size.z) < 3.0:
		return
	var ar := Area3D.new()
	ar.collision_layer = VRSTVA_VODA
	ar.collision_mask = 0
	ar.monitoring = false
	var cs := CollisionShape3D.new()
	cs.shape = am.create_trimesh_shape()
	ar.add_child(cs)
	mi.add_child(ar)


# ------------------------------------------------------------------ kolize

func _trimesh(mi: MeshInstance3D) -> void:
	var body := StaticBody3D.new()
	body.name = String(mi.name) + "_kolize"
	var cs := CollisionShape3D.new()
	cs.shape = mi.mesh.create_trimesh_shape()
	body.add_child(cs)
	mi.add_child(body)


func _collisions(parent: Node3D) -> void:
	var body := StaticBody3D.new()
	body.name = "Kolize"
	parent.add_child(body)
	for c: Array in data["kolize"]:
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(absf(c[7]), absf(c[8]), absf(c[9])).max(Vector3(0.02, 0.02, 0.02))
		cs.shape = box
		cs.transform = Transform3D(Basis(Quaternion(c[4], c[5], c[6], c[3]).normalized()), Vector3(c[0], c[1], c[2]))
		body.add_child(cs)


# ------------------------------------------------------------------ informace pro hru

func _info() -> void:
	info["mista"] = data.get("nazvy_mist", [])          # ruiny a jina pojmenovana mista v krajine
	for r: Dictionary in data["mistnosti"]:
		var a: Array = r["ambient"]
		if r.has("yaw"):
			# otocena mistnost (chalupy ve vsi): stred podlahy, rozmery v ramci domu
			var sz: Vector3 = _v3(r["size"])
			var xf := Transform3D(Basis(Vector3.UP, float(r["yaw"])), _v3(r["pos"]))
			info["rooms"].append({"name": r["name"], "title": String(r.get("title", "")), "inv": xf.affine_inverse(), "c": xf.origin,
					"aabb": AABB(Vector3(-sz.x / 2, 0, -sz.z / 2), sz), "ambient": Color(a[0], a[1], a[2])})
			continue
		info["rooms"].append({"name": r["name"], "aabb": AABB(_v3(r["pos"]), _v3(r["size"])),
				"ambient": Color(a[0], a[1], a[2])})
	for fdat: Dictionary in data["ohne"]:
		var d := fdat.duplicate()
		d["pos"] = _v3(fdat["pos"])
		d["night_only"] = false
		info["fires"].append(d)
	for u: Dictionary in data["pouziti"]:
		var d2 := u.duplicate()
		d2["pos"] = _v3(u["pos"])
		info["use"].append(d2)
	for s: Array in data["kour"]:
		info["smoke"].append(_v3(s))


# ------------------------------------------------------------------ rostliny

const NIZKE := ["divoka_trava", "grass_medium_01", "grass_medium_02", "dandelion_01", "nettle_plant", "fern_02",
		"kamen_maly_1", "kamen_maly_2", "kamen_maly_3", "kamen_maly_4", "kamen_maly_5"]
const STREDNI := ["shrub_02", "sipek", "fir_sapling", "rock_moss_set_01", "dry_branches_medium_01", "tree_stump_01",
		"kamen_zula_1", "kamen_zula_2", "kamen_piskovec_1", "kamen_piskovec_2", "kamen_droba_1",
		"orobinec_1", "orobinec_2", "rakos_1", "rakos_2", "bez_cerny_1", "bez_cerny_2", "bez_cerny_3"]
## Podrost z druheho chatu (jen zblizka) a dvojice strom / vzdalena verze (prepnuti kolem 60 m).
const PODROST := ["kapradi_1", "kapradi_2", "kapradi_3", "mech_1", "mech_2", "mech_3", "celandine_01", "periwinkle_plant", "moss_01"]
const LOD_M := 220.0
## Stromy zdalky: misto modelu z karet (zdalky ploche "placky") plny nizkopolygonovy tvar stejne velikosti
## (smrk vrstvene kuzely, listnac hrouda koruny); zblizka plny strom. Karty <model>_daleko se uz nepouzivaji.
const STROM_PREP := 60.0
const SKALA_LOD0 := 40.0
const SKALA_LOD1 := 120.0
const STROM_DOHLED := 120.0                # rozpocet: za 120 m zadne stromy (radeji prazdny obzor nez pad)
const LISTNACE := ["lipa", "dub", "briza", "vrba", "buk", "olse", "borovice"]
var _tvary := {}


func _strom_tvar(kind: String) -> String:
	if kind == "smrk" or kind.begins_with("smrk_"):
		return "smrk"
	for l: String in LISTNACE:
		if kind == l or kind.begins_with(l + "_"):
			return l
	return ""


## Plny tvar stromu do obrysu (aabb) puvodniho modelu: barva z vrcholu, dole tmavsi (zdalky objem, ne list papiru).
func _tvar_mesh(druh: String, bb: AABB) -> Mesh:
	var key := "%s_%d_%d" % [druh, int(bb.size.y * 10), int(bb.size.x * 10)]
	if _tvary.has(key):
		return _tvary[key]
	var r := RandomNumberGenerator.new()
	r.seed = hash(key)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c := bb.get_center()
	var y0 := bb.position.y
	var h := bb.size.y
	var rad := minf(bb.size.x, bb.size.z) * 0.5
	var kura := Color(0.2, 0.15, 0.1) if druh != "briza" else Color(0.6, 0.58, 0.52)
	var zel: Color = {"smrk": Color(0.07, 0.13, 0.06), "briza": Color(0.2, 0.28, 0.1), "vrba": Color(0.2, 0.26, 0.14),
			"borovice": Color(0.1, 0.16, 0.07),
			"olse": Color(0.11, 0.19, 0.07)}.get(druh, Color(0.14, 0.22, 0.08))
	# kmen
	var kr := maxf(h * 0.012, 0.12)
	_valec(st, Vector3(c.x, y0, c.z), kr, kr * 0.6, h * (0.5 if druh == "smrk" else 0.45), 5, kura, kura)
	if druh == "smrk":
		# patra kuzelu, kazde nize sirsi, zubaty okraj (vetve)
		var pater := 5
		var dole := y0 + h * 0.12
		for i in pater:
			var t0 := float(i) / pater
			var ya := dole + (h - (dole - y0)) * t0 * 0.92
			var yb := ya + (h - (dole - y0)) * 0.34
			if i == pater - 1:
				yb = y0 + h
			var rr := rad * (1.0 - t0 * 0.82) * r.randf_range(0.9, 1.05)
			_kuzel(st, Vector3(c.x, ya, c.z), rr, yb - ya, 9, r, zel * 0.6, zel * 1.15)
	else:
		# koruna: shluk hrud (zploštělé koule s nerovnym povrchem)
		var kz := y0 + h * (0.55 if druh == "borovice" else (0.32 if druh != "vrba" else 0.4))
		var kv := y0 + h - kz
		var n := 5 if rad > 3.0 else 4
		_hruda(st, Vector3(c.x, kz + kv * 0.5, c.z), Vector3(rad * 0.8, kv * 0.5, rad * 0.8), r, zel)
		for i in n:
			var a := TAU * i / n + r.randf() * 0.6
			var d := rad * r.randf_range(0.35, 0.55)
			var p := Vector3(c.x + cos(a) * d, kz + kv * r.randf_range(0.35, 0.65), c.z + sin(a) * d)
			var s := rad * r.randf_range(0.45, 0.6)
			_hruda(st, p, Vector3(s, minf(s, kv * 0.4), s), r, zel * r.randf_range(0.9, 1.1))
	st.generate_normals()
	var mesh := st.commit()
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 1.0
	mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT_WRAP
	mesh.surface_set_material(0, mat)
	_tvary[key] = mesh
	return mesh


func _valec(st: SurfaceTool, b: Vector3, r0: float, r1: float, h: float, n: int, c0: Color, c1: Color) -> void:
	for i in n:
		var a0 := TAU * i / n
		var a1 := TAU * (i + 1) / n
		var p0 := b + Vector3(cos(a0) * r0, 0, sin(a0) * r0)
		var p1 := b + Vector3(cos(a1) * r0, 0, sin(a1) * r0)
		var q0 := b + Vector3(cos(a0) * r1, h, sin(a0) * r1)
		var q1 := b + Vector3(cos(a1) * r1, h, sin(a1) * r1)
		for v: Array in [[p0, c0], [q0, c1], [q1, c1], [p0, c0], [q1, c1], [p1, c0]]:
			st.set_color(v[1])
			st.add_vertex(v[0])


func _kuzel(st: SurfaceTool, b: Vector3, rr: float, h: float, n: int, r: RandomNumberGenerator, c0: Color, c1: Color) -> void:
	var spic := b + Vector3(0, h, 0)
	var okraj: Array = []
	for i in n * 2:
		# zuby: stridave dal a bliz, konce vetvi lehce dolu
		var a := TAU * i / (n * 2) + r.randf_range(-0.1, 0.1)
		var d := rr * (1.0 if i % 2 == 0 else 0.62) * r.randf_range(0.85, 1.1)
		okraj.append(b + Vector3(cos(a) * d, -h * (0.08 if i % 2 == 0 else 0.0), sin(a) * d))
	var m := okraj.size()
	for i in m:
		var a: Vector3 = okraj[i]
		var bb: Vector3 = okraj[(i + 1) % m]
		for v: Array in [[a, c0], [spic, c1], [bb, c0]]:
			st.set_color(v[1])
			st.add_vertex(v[0])
		# spodek patra (tmavy, zdola nevidet skrz)
		for v: Array in [[a, c0 * 0.5], [bb, c0 * 0.5], [b + Vector3(0, h * 0.2, 0), c0 * 0.4]]:
			st.set_color(v[1])
			st.add_vertex(v[0])


func _hruda(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator, zel: Color) -> void:
	var ny := 4
	var nx := 9
	var body: Array = []
	for j in ny + 1:
		var row: Array = []
		var th := PI * j / ny
		for i in nx:
			var ph := TAU * i / nx
			var k := 1.0 if j == 0 or j == ny else r.randf_range(0.8, 1.15)
			var d := Vector3(sin(th) * cos(ph), cos(th), sin(th) * sin(ph))
			row.append(cen + Vector3(d.x * sz.x, d.y * sz.y, d.z * sz.z) * k)
		body.append(row)
	for j in ny:
		for i in nx:
			var a: Vector3 = body[j][i]
			var b: Vector3 = body[j][(i + 1) % nx]
			var c2: Vector3 = body[j + 1][i]
			var d2: Vector3 = body[j + 1][(i + 1) % nx]
			for v: Vector3 in [a, b, d2, a, d2, c2]:
				# nahore svetlejsi (slunce), dole tmavy stin koruny
				var t := clampf((v.y - cen.y) / sz.y * 0.5 + 0.5, 0.0, 1.0)
				st.set_color(zel * lerpf(0.45, 1.2, t))
				st.add_vertex(v)


func _plants(parent: Node3D, quality: int) -> void:
	var root := Node3D.new()
	root.name = "Rostliny"
	parent.add_child(root)
	var keep_low: float = [0.3, 0.6, 1.0][quality]
	var keep_tree: float = [0.5, 0.8, 1.0][quality]
	var grass_mat := material("trava_divoka")
	var scenes := {}
	# zakladni modely pred vzdalenymi verzemi: vzdalene LOD pak sdili materialy (a textury) zakladniho modelu
	var klice: Array = data["rostliny"].keys()
	klice.sort_custom(func(x: String, y: String) -> bool: return int(x.contains("_daleko")) < int(y.contains("_daleko")))
	var mat_zaklad := {}                 # druh -> {jmeno materialu: Material}
	for key: String in klice:
		var kind := key.substr(0, key.rfind("_"))
		if not scenes.has(kind):
			var path := MOD + "rostliny/%s.glb" % kind
			if not ResourceLoader.exists(path):
				scenes[kind] = null
			else:
				scenes[kind] = (load(path) as PackedScene).instantiate()
		var inst: Node = scenes[kind]
		if inst == null:
			continue
		var mesh: Mesh = null
		for n in inst.find_children("*", "MeshInstance3D", true, false):
			if String(n.name) == key:
				mesh = (n as MeshInstance3D).mesh
		if mesh == null:
			continue
		if kind.contains("_daleko"):
			# LOD1/LOD2: stejne materialy jako plny model (jinak 3 kopie stejnych textur v graficke pameti)
			var zk: String = kind.left(kind.find("_daleko"))
			if mat_zaklad.has(zk):
				mesh = mesh.duplicate()
				for i in mesh.get_surface_count():
					var om := mesh.surface_get_material(i)
					var nm2 := om.resource_name if om else ""
					if (mat_zaklad[zk] as Dictionary).has(nm2):
						mesh.surface_set_material(i, mat_zaklad[zk][nm2])
		elif not mat_zaklad.has(kind):
			var md := {}
			for i in mesh.get_surface_count():
				var om := mesh.surface_get_material(i)
				if om:
					md[om.resource_name] = om
			mat_zaklad[kind] = md
		if kind == "divoka_trava":
			mesh = mesh.duplicate()
			for i in mesh.get_surface_count():
				var nm := mesh.surface_get_material(i).resource_name if mesh.surface_get_material(i) else ""
				mesh.surface_set_material(i, material(nm) if nm != "" else grass_mat)
		if kind == "divoka_trava" or kind == "grass_medium_01":
			continue                      # travu dela louka (louka.gd); tyto trsy ji jen zdvojovaly (3,6 M troj. u tvrze)
		var low := NIZKE.has(kind) or PODROST.has(kind)
		var daleko := kind.ends_with("_daleko")
		if daleko and not kind.begins_with("skala_"):
			continue
		var tvar := _strom_tvar(kind)
		var tvar_mesh: Mesh = _tvar_mesh(tvar, mesh.get_aabb()) if tvar != "" else null
		var ma_lod: bool = data["rostliny"].has(kind + "_daleko_0")
		var mid := STREDNI.has(kind)
		var keep := keep_low if low else (keep_tree if not mid else 1.0)
		var cells := {}
		var k := 0
		for t: Array in data["rostliny"][key]:
			k += 1
			if keep < 1.0 and fmod(k * 0.6180339, 1.0) > keep:
				continue
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])),
					Vector3(t[3], t[7], t[11]))
			var c := Vector2i(floori(xf.origin.x / BUNKA), floori(xf.origin.z / BUNKA))
			if not cells.has(c):
				cells[c] = []
			cells[c].append(xf)
		for c: Vector2i in cells:
			var list: Array = cells[c]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = mesh
			mm.instance_count = list.size()
			for i in list.size():
				mm.set_instance_transform(i, list[i])
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.name = "%s_%d_%d" % [key, c.x, c.y]
			if SBER.has(kind):
				for i in list.size():
					sber_spots.append({"id": SBER[kind], "mmi": mmi, "i": i, "xf": list[i]})
			# ROZPOCET (1500 kresleni, 2 M troj.): skaly LOD0 do 40 m (jen ta vrha stin), LOD1 40-120 m, LOD2 dal;
			# stromy plne do 60 m (stin), dal jednoduchy tvar bez stinu; ostatni vegetace stiny nevrha vubec
			var stin_ok := quality > 0
			var off := GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var on := GeometryInstance3D.SHADOW_CASTING_SETTING_ON if stin_ok else off
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
			mmi.cast_shadow = off
			if tvar_mesh:
				mmi.visibility_range_end = STROM_PREP
				mmi.visibility_range_end_margin = 10.0
				mmi.cast_shadow = on
				var mm2 := MultiMesh.new()
				mm2.transform_format = MultiMesh.TRANSFORM_3D
				mm2.mesh = tvar_mesh
				mm2.instance_count = list.size()
				for i in list.size():
					mm2.set_instance_transform(i, list[i])
				var far := MultiMeshInstance3D.new()
				far.multimesh = mm2
				far.name = mmi.name + "_tvar"
				far.visibility_range_begin = STROM_PREP - 5.0
				far.visibility_range_begin_margin = 10.0
				far.visibility_range_end = STROM_DOHLED
				far.visibility_range_end_margin = 15.0
				far.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
				far.cast_shadow = off
				root.add_child(far)
			elif kind.begins_with("skala_"):
				if kind.ends_with("_daleko2"):
					mmi.visibility_range_begin = SKALA_LOD1
					mmi.visibility_range_end = 500.0
					mmi.visibility_range_end_margin = 40.0
				elif daleko:
					mmi.visibility_range_begin = SKALA_LOD0
					mmi.visibility_range_end = SKALA_LOD1
					mmi.visibility_range_end_margin = 10.0
				else:
					mmi.visibility_range_end = SKALA_LOD0
					mmi.visibility_range_end_margin = 5.0
					mmi.cast_shadow = on
			elif daleko:
				mmi.visibility_range_begin = LOD_M
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
			elif ma_lod:
				mmi.visibility_range_end = LOD_M
			elif low:
				mmi.visibility_range_end = [26.0, 40.0, 55.0][quality]
				mmi.visibility_range_end_margin = 6.0
			elif mid:
				mmi.visibility_range_end = [60.0, 90.0, 120.0][quality]
				mmi.visibility_range_end_margin = 10.0
			else:
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
				mmi.visibility_range_end_margin = 40.0
			root.add_child(mmi)
	for kind: String in scenes:
		if scenes[kind]:
			(scenes[kind] as Node).free()


## Trava ve vsi: husté levne trsy (3 zkrizene karty) podle mrizky z Blenderu (vyska terenu, hustota).
## Na cestach, ve dvorech a v domech nic, u plotu a na loukach husteji.
func _ves_grass(parent: Node3D, quality: int) -> void:
	var g: Dictionary = data.get("trava_ves", {})
	if g.is_empty():
		return
	var n := int(g["n"])
	var k := float(g["k"])
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var ms := Marshalls.base64_to_raw(String(g["m"]))
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = load("res://obrazky/trava_karta.png")
	mat.albedo_color = Color(0.6, 0.64, 0.44)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.45
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.85
	mat.backlight_enabled = true
	mat.backlight = Color(0.22, 0.27, 0.08)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for q in 3:
		var ang := PI * q / 3.0
		var tg := Vector3(cos(ang), 0, sin(ang)) * 0.4
		var up := Vector3(0, 0.6, 0)
		var pts := [-tg, tg, tg + up, -tg + up]
		var uvs := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		var cols := [Color(0.55, 0.58, 0.5), Color(0.55, 0.58, 0.5), Color(1, 1, 1), Color(1, 1, 1)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_color(cols[i])
			st.set_uv(uvs[i])
			st.set_normal(Vector3.UP)
			st.add_vertex(pts[i])
	var mesh := st.commit()
	mesh.surface_set_material(0, mat)
	grass_mesh = mesh
	return                                        # travu ve vsi dela louka.gd (mrizka trava_ves)
	var step: float = [0.95, 0.75, 0.62][quality]
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var cells := {}
	var lim := (n - 1) * k
	var x := 0.0
	while x < lim:
		var z := 0.0
		while z < lim:
			var px := x + rng.randf_range(-0.4, 0.4) * step
			var pz := z + rng.randf_range(-0.4, 0.4) * step
			z += step
			if px < 0.0 or pz < 0.0 or px >= lim or pz >= lim:
				continue
			var i := int(px / k)
			var j := int(pz / k)
			var fx := px / k - i
			var fz := pz / k - j
			var a0 := j * n + i
			var dens := lerpf(lerpf(ms[a0], ms[a0 + 1], fx), lerpf(ms[a0 + n], ms[a0 + n + 1], fx), fz) / 255.0
			if rng.randf() > dens * 1.1:
				continue
			var h0 := ys.decode_s16(a0 * 2)
			var h1 := ys.decode_s16((a0 + 1) * 2)
			var h2 := ys.decode_s16((a0 + n) * 2)
			var h3 := ys.decode_s16((a0 + n + 1) * 2)
			var hy := lerpf(lerpf(h0, h1, fx), lerpf(h2, h3, fx), fz) / 100.0
			var sc := rng.randf_range(0.55, 1.2) * lerpf(0.7, 1.1, dens)
			var xf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, sc * rng.randf_range(0.75, 1.35), sc)),
					Vector3(x0 + px, hy - 0.04, z0 + pz))
			var c := Vector2i(floori(xf.origin.x / BUNKA), floori(xf.origin.z / BUNKA))
			if not cells.has(c):
				cells[c] = []
			cells[c].append(xf)
		x += step
	var root := Node3D.new()
	root.name = "TravaVes"
	parent.add_child(root)
	var total := 0
	for c: Vector2i in cells:
		var list: Array = cells[c]
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
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_end = [30.0, 42.0, 55.0][quality]
		mmi.visibility_range_end_margin = 8.0
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		root.add_child(mmi)
		total += list.size()
	print("trava ve vsi: ", total, " trsu")


## Pevne predmety z katalogu (bozi muka na krizovatce): model z modely/predmety, kolize kvadrem.
func _static_items(parent: Node3D) -> void:
	var katalog: Dictionary = {}
	var fk := FileAccess.open(MOD + "predmety.json", FileAccess.READ)
	if fk:
		katalog = JSON.parse_string(fk.get_as_text())
	for it: Dictionary in data.get("staticke", []):
		var id := String(it["id"])
		var ps: PackedScene = load(MOD + "predmety/" + id + ".glb")
		if ps == null:
			continue
		var n := Node3D.new()
		n.name = "Staticky_" + id
		var a: Array = it["p"]
		n.position = Vector3(a[0], a[1], a[2])
		n.rotation.y = float(it.get("yaw", 0.0))
		parent.add_child(n)
		n.add_child(ps.instantiate())
		if it.has("boxy"):
			# stavba s jednoduchymi kolizemi (stan: stoly, sudy, platno; provazy a koliky bez kolize)
			var sb := StaticBody3D.new()
			for q: Array in it["boxy"]:
				var c := CollisionShape3D.new()
				var bx := BoxShape3D.new()
				bx.size = Vector3(q[3], q[4], q[5])
				c.shape = bx
				c.position = Vector3(q[0], q[1], q[2])
				sb.add_child(c)
			n.add_child(sb)
			continue
		if String(it.get("kolize", "")) == "trimesh":
			# stavba (hostinec, stan): presna kolize ze site, dovnitr se da vejit
			for mi in n.find_children("*", "MeshInstance3D", true, false):
				_trimesh(mi as MeshInstance3D)
				(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
			continue
		var r: Array = katalog.get(id, {}).get("rozmer", [1.0, 1.0, 1.0])
		var b := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = Vector3(float(r[0]) * 0.7, float(r[1]), float(r[2]) * 0.7)
		cs.shape = bs
		cs.position.y = float(r[1]) * 0.5
		b.add_child(cs)
		n.add_child(b)
