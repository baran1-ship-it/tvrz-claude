extends RefCounted
## Svet tvrze vymodelovany v Blenderu (blender/export_game.py): nacte modely/tvrz.glb,
## priradi materialy podle jmen, postavi kolize, rostliny (MultiMesh po bunkach) a predá
## informace o ohnich, mistnostech a pouzitelnych vecech hernimu zivotu (life.gd).

const MOD := "res://modely/"
const BUNKA := 24.0
## textury s vyskovou mapou -> parallax (hloubka v metrech)
const HLOUBKA := {"dlazba": 0.04, "dlazba_hrad": 0.035, "kocicky": 0.05, "piskovec": 0.02, "podlaha": 0.008, "prkna_ven": 0.012, "sindel": 0.035}

var info: Dictionary
var data: Dictionary
var sum: NoiseTexture2D
var _tex := {}
var _mats := {}
var water_y := -2.75


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
		if nm.begins_with("Rakos") or nm.begins_with("Slama"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_end = 70.0
	_collisions(parent)
	_info()
	_plants(parent, quality)


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
			if tx == "sindel":
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("skvrny", 1.0)
			if HLOUBKA.has(tx) and (String(d["coord"]) == "world" or tx == "sindel"):
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
			var s4 := ShaderMaterial.new()
			s4.shader = load("res://shaders/rybnik.gdshader")
			s4.set_shader_parameter("sum", sum)
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
			var w := StandardMaterial3D.new()
			w.albedo_color = Color(0.03, 0.04, 0.035)
			w.roughness = 0.05
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
			mi.set_surface_override_material(i, material(nm))


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
	for r: Dictionary in data["mistnosti"]:
		var a: Array = r["ambient"]
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

const NIZKE := ["divoka_trava", "grass_medium_01", "grass_medium_02", "dandelion_01", "nettle_plant", "fern_02"]
const STREDNI := ["shrub_02", "fir_sapling", "rock_moss_set_01", "dry_branches_medium_01", "tree_stump_01"]


func _plants(parent: Node3D, quality: int) -> void:
	var root := Node3D.new()
	root.name = "Rostliny"
	parent.add_child(root)
	var keep_low: float = [0.3, 0.6, 1.0][quality]
	var keep_tree: float = [0.5, 0.8, 1.0][quality]
	var grass_mat := material("trava_divoka")
	var scenes := {}
	for key: String in data["rostliny"]:
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
		if kind == "divoka_trava":
			mesh = mesh.duplicate()
			for i in mesh.get_surface_count():
				var nm := mesh.surface_get_material(i).resource_name if mesh.surface_get_material(i) else ""
				mesh.surface_set_material(i, material(nm) if nm != "" else grass_mat)
		var low := NIZKE.has(kind)
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
			if low:
				mmi.visibility_range_end = [26.0, 40.0, 55.0][quality]
				mmi.visibility_range_end_margin = 6.0
				mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			elif mid:
				mmi.visibility_range_end = [60.0, 90.0, 130.0][quality]
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if quality == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			else:
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if quality == 0 else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			root.add_child(mmi)
	for kind: String in scenes:
		if scenes[kind]:
			(scenes[kind] as Node).free()
