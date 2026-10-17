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
		if nm == "Reka_voda" and FileAccess.file_exists("res://modely/reka/reka.res"):
			mi.visible = false               # potok: Waterways (_reka), mrizkova hladina se zubatym brehem pryc
		if nm == "Teren_cesta_kamen":
			mi.visible = false               # tmave kocici hlavy pres cestu s ostrou hranou (Misa 17. 10.): pod nimi je cesta
			continue
		if nm == "Skaly":
			mi.visible = false               # zaoblene balvany u tvrze: textura ze sveta v "letokruzich" (Misa: smazat)
		if nm.begins_with("Teren") or nm.begins_with("Nadvori"):
			_trimesh(mi)
		if nm.begins_with("Teren") or nm.begins_with("Reka") or nm.begins_with("Ruiny") or nm.begins_with("Skaly") \
				or nm.ends_with("_zahrady") or nm.begins_with("Hnojiste"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # rozpocet: teren, voda, ruiny, zahrady nekreslit do stinu
		if nm.begins_with("Rakos") or nm.begins_with("Slama"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_end = 70.0
	_reka(parent)
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


var _alb := {}


func _albedo() -> Dictionary:
	if _alb.is_empty() and FileAccess.file_exists(MOD + "textury/albedo.json"):
		_alb = JSON.parse_string(FileAccess.get_file_as_string(MOD + "textury/albedo.json"))
	return _alb


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
			s3.set_shader_parameter("louka_a", _t("louka", "diff"))
			s3.set_shader_parameter("louka_n", _t("louka", "nor"))
			s3.set_shader_parameter("letecky_a", _t("louka_letecky", "diff"))
			s3.set_shader_parameter("louka_dal_a", _t("louka_dal", "diff"))
			s3.set_shader_parameter("louka_dal_m", _size("louka_dal"))
			s3.set_shader_parameter("obili_a", _t("pole_obili", "diff"))
			s3.set_shader_parameter("oranice_a", _t("pole_oranice", "diff"))
			s3.set_shader_parameter("obili_m", _size("pole_obili"))
			# kalibrace odrazivosti: fotka * (skutecna odrazivost povrchu / prumer fotky), viz tools/albedo_textur.py
			for u: Array in [["hlina_k", "hlina", 0.08], ["louka_k", "louka", 0.10], ["louka_dal_k", "louka_dal", 0.09],
					["hrabanka_k", "hrabanka", 0.08], ["obili_k", "pole_obili", 0.20], ["oranice_k", "pole_oranice", 0.10]]:
				s3.set_shader_parameter(u[0], u[2] / maxf(float(_albedo().get(u[1], u[2])), 0.01))
			s3.set_shader_parameter("oranice_m", _size("pole_oranice"))
			s3.set_shader_parameter("hrabanka_a", _t("hrabanka", "diff"))
			s3.set_shader_parameter("hlina_m", _size("hlina"))
			s3.set_shader_parameter("louka_m", _size("louka"))
			s3.set_shader_parameter("letecky_m", _size("louka_letecky"))
			s3.set_shader_parameter("hrabanka_m", _size("hrabanka"))
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
			s4.set_shader_parameter("kalnost", 0.35 if tek > 0.5 else 0.82)
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

## Potok z Waterways (tools/reka_bake.gd): sit s hloubkou ve vrcholech, mapy proudeni a peny, shader pro Compatibility.
func _reka(parent: Node3D) -> void:
	if not FileAccess.file_exists("res://modely/reka/reka.res"):
		return
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://modely/reka/reka.json"))
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/reka.gdshader")
	m.set_shader_parameter("normal_bump_texture", load("res://modely/reka/water1_normal_bump.png"))
	m.set_shader_parameter("i_texture_foam_noise", load("res://modely/reka/foam_noise.png"))
	m.set_shader_parameter("i_flowmap", load("res://modely/reka/reka_flow.png"))
	m.set_shader_parameter("i_distmap", load("res://modely/reka/reka_dist.png"))
	m.set_shader_parameter("i_valid_flowmap", true)
	m.set_shader_parameter("i_uv2_sides", int(meta["uv2_sides"]))
	m.set_shader_parameter("flow_speed", 0.3)
	m.set_shader_parameter("normal_scale", 0.6)
	m.set_shader_parameter("roughness", 0.15)
	m.set_shader_parameter("foam_amount", 1.2)
	m.set_shader_parameter("foam_color", Color(0.7, 0.72, 0.66, 0.6))
	# barvy v linearnim prostoru (source_color): melka hnedozelena, hluboka tmava; tablet bez HDR = tmavsi nez navrh
	m.set_shader_parameter("melka", Color(0.24, 0.27, 0.15))
	m.set_shader_parameter("hluboka", Color(0.06, 0.08, 0.05))
	m.set_shader_parameter("hloubka_barvy", 0.8)
	var mi := MeshInstance3D.new()
	mi.name = "Potok"
	mi.mesh = load("res://modely/reka/reka.res")
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)


func _trimesh(mi: MeshInstance3D) -> void:
	var body := StaticBody3D.new()
	body.name = String(mi.name) + "_kolize"
	var cs := CollisionShape3D.new()
	var tri := mi.mesh.create_trimesh_shape()
	# oboustranne: modely ze SketchUpu maji cast ploch otocenych (podlaha hostince normalou dolu) - jednostranna
	# kolize hrace shora propustila na teren pod podlahou a zespodu ho drzela (zaseknuti ve dverich a na schodech)
	tri.backface_collision = true
	cs.shape = tri
	body.add_child(cs)
	mi.add_child(body)


func _collisions(parent: Node3D) -> void:
	var body := StaticBody3D.new()
	body.name = "Kolize"
	parent.add_child(body)
	# skalni veze: misto kvadru kolem cele veze konvexni obal modelu (na vrcholu se stoji na skale, ne nad stromem)
	var veze := {}
	for key: String in data["rostliny"]:
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var ps: PackedScene = load("res://modely/rostliny/%s.glb" % key.trim_suffix("_0"))
		if ps == null:
			continue
		var inst := ps.instantiate()
		var tvar: Shape3D = null
		for m in inst.find_children("*", "MeshInstance3D", true, false):
			var me := (m as MeshInstance3D).mesh
			if me.get_surface_count() > 0 and me.surface_get_material(0) and String(me.surface_get_material(0).resource_name).begins_with("skala"):
				tvar = me.create_convex_shape(true, true)
				break
		inst.free()
		if tvar == null:
			continue
		for t: Array in data["rostliny"][key]:
			veze[Vector2i(roundi(float(t[3]) * 2.0), roundi(float(t[11]) * 2.0))] = true
			var cs := CollisionShape3D.new()
			cs.shape = tvar
			cs.transform = Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11]))
			body.add_child(cs)
	for c: Array in data["kolize"]:
		if veze.has(Vector2i(roundi(float(c[0]) * 2.0), roundi(float(c[2]) * 2.0))) and absf(c[8]) > 5.0:
			continue
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
func _tvar_mesh(druh: String, bb: AABB, listi: Material = null) -> Mesh:
	var key := "%s_%d_%d_%d" % [druh, int(bb.size.y * 10), int(bb.size.x * 10), listi.get_instance_id() if listi else 0]
	if _tvary.has(key):
		return _tvary[key]
	var r := RandomNumberGenerator.new()
	r.seed = hash(key)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# obal koruny s texturou listi stromu (pruhledne mezery), pod nim tmave jadro - ne hladke jednobarevne koule
	var st2: SurfaceTool = null
	if listi and druh != "smrk":
		st2 = SurfaceTool.new()
		st2.begin(Mesh.PRIMITIVE_TRIANGLES)
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
		_hruda(st, Vector3(c.x, kz + kv * 0.5, c.z), Vector3(rad * 0.8, kv * 0.5, rad * 0.8), r, zel, st2)
		for i in n:
			var a := TAU * i / n + r.randf() * 0.6
			var d := rad * r.randf_range(0.35, 0.55)
			var p := Vector3(c.x + cos(a) * d, kz + kv * r.randf_range(0.35, 0.65), c.z + sin(a) * d)
			var s := rad * r.randf_range(0.45, 0.6)
			_hruda(st, p, Vector3(s, minf(s, kv * 0.4), s), r, zel * r.randf_range(0.9, 1.1), st2)
	st.generate_normals()
	var mesh := st.commit()
	if st2:
		st2.generate_normals()
		st2.commit(mesh)
		var lm := listi.duplicate() as Material
		if lm is BaseMaterial3D:
			(lm as BaseMaterial3D).cull_mode = BaseMaterial3D.CULL_DISABLED
		mesh.surface_set_material(1, lm)
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


func _hruda(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator, zel: Color, st2: SurfaceTool = null) -> void:
	if st2:
		_obal(st2, cen, sz * 1.12, r)
		sz *= 0.82
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


func _listi(mesh: Mesh) -> Material:
	# material listi stromu: povrch s pruhlednosti (alfa) - ten se pouzije na obal vzdalene koruny
	for i in mesh.get_surface_count():
		var m := mesh.surface_get_material(i)
		if m is BaseMaterial3D and (m as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED \
				and (m as BaseMaterial3D).albedo_texture:
			return m
	return null


func _obal(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator) -> void:
	# koule s UV pro texturu listi (opakuje se zhruba po 2,5 m), nerovny povrch
	var ny := 4
	var nx := 9
	var rep := maxf(1.0, maxf(sz.x, sz.y) / 1.25)
	var body: Array = []
	for j in ny + 1:
		var row: Array = []
		var th := PI * j / ny
		for i in nx + 1:
			var ph := TAU * i / nx
			var k := 1.0 if j == 0 or j == ny or i == nx else r.randf_range(0.85, 1.12)
			var d := Vector3(sin(th) * cos(ph), cos(th), sin(th) * sin(ph))
			row.append(cen + Vector3(d.x * sz.x, d.y * sz.y, d.z * sz.z) * k)
		if j > 0 and j < ny:
			row[nx] = row[0]
		body.append(row)
	for j in ny:
		for i in nx:
			var q := [[j, i], [j, i + 1], [j + 1, i + 1], [j, i], [j + 1, i + 1], [j + 1, i]]
			for ij: Array in q:
				st.set_uv(Vector2(float(ij[1]) / nx * rep * 2.0, float(ij[0]) / ny * rep))
				st.add_vertex(body[ij[0]][ij[1]])


const IMP_BUNKA := 256.0
const IMP_DOHLED := 900.0
var _imp_meta := {}


func _imp_druh(kind: String) -> String:
	if _imp_meta.is_empty() and FileAccess.file_exists("res://obrazky/impostory/impostory.json"):
		_imp_meta = JSON.parse_string(FileAccess.get_file_as_string("res://obrazky/impostory/impostory.json"))
	if _imp_meta.has(kind):
		return kind
	for d: String in _imp_meta:
		if kind.begins_with(d) or (d == "vrba" and kind.begins_with("vrba")):
			return d
	return ""


## Impostory: jeden ctverec na strom, MultiMesh po druzich a bunkach 256 m, jednotkove transformace
## (poloha v INSTANCE_CUSTOM), obal bunky rucne (jinak by Godot videl vsechny instance v pocatku).
func _impostory(root: Node3D, imp: Dictionary) -> void:
	var quad := ArrayMesh.new()
	var a := []
	a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-1, 0, 0), Vector3(1, 0, 0), Vector3(1, 2, 0), Vector3(-1, 2, 0)])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	quad.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	var n := 0
	for d: String in imp:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/impostor.gdshader")
		m.set_shader_parameter("barva", load("res://obrazky/impostory/%s_a.png" % d))
		m.set_shader_parameter("normaly", load("res://obrazky/impostory/%s_n.png" % d))
		var st: Array = _imp_meta[d]["stred"]
		m.set_shader_parameter("stred", Vector3(st[0], st[1], st[2]))
		m.set_shader_parameter("polomer", float(_imp_meta[d]["polomer"]))
		m.set_shader_parameter("fade_od", STROM_PREP - 10.0)
		m.set_shader_parameter("fade_do", IMP_DOHLED)
		for bc: Vector2i in imp[d]:
			var list: Array = imp[d][bc]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			mm.mesh = quad
			mm.instance_count = list.size()
			var lo := Vector3(INF, INF, INF)
			var hi := -lo
			for i in list.size():
				var c: Color = list[i]
				mm.set_instance_transform(i, Transform3D.IDENTITY)
				mm.set_instance_custom_data(i, c)
				lo = lo.min(Vector3(c.r, c.g, c.b))
				hi = hi.max(Vector3(c.r, c.g, c.b))
			var r := float(_imp_meta[d]["polomer"]) * 2.5
			mm.custom_aabb = AABB(lo - Vector3(r, r, r), hi - lo + Vector3(r, r, r) * 2.0)
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.material_override = m
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.name = "impostor_%s_%d_%d" % [d, bc.x, bc.y]
			root.add_child(mmi)
			n += list.size()
	print("impostory: %d stromu" % n)


## Realie 1393 (Misa, radce 09:20): smrk v niznim udoli nerostl. Pod 25 m nad tvrzi (udoli, okoli vsi, louky)
## nahradit smrk dubohabrinou (dub, buk, lipa); na hrebenech, ve skalnim meste a jako primes (15 %) zustava.
func _skala_detail(om: BaseMaterial3D) -> Material:
	var m := ShaderMaterial.new()
	m.resource_name = om.resource_name
	m.shader = load("res://shaders/skala_detail.gdshader")
	m.set_shader_parameter("barva", om.albedo_texture)
	m.set_shader_parameter("normala", om.normal_texture)
	m.set_shader_parameter("detail", _t("skala_piskovec", "diff"))
	m.set_shader_parameter("detail_n", _t("skala_piskovec", "nor"))
	m.set_shader_parameter("detail_m", _size("skala_piskovec"))
	m.set_shader_parameter("detail_prumer", float(_albedo().get("skala_piskovec", 0.2)))   # linearni, jako textura v shaderu
	return m


func _smrky_na_listnace() -> void:
	var r: Dictionary = data["rostliny"]
	var cile := ["dub_stredni_0", "buk_stredni_0", "lipa_stredni_0", "dub_stredni_0"]
	if not cile.all(func(k: String) -> bool: return r.has(k)):
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var n := 0
	for key: String in r.keys():
		if not key.begins_with("smrk_") or key.contains("_daleko"):
			continue
		var zustava: Array = []
		for t: Array in r[key]:
			if float(t[7]) < 25.0 and rng.randf() > 0.15:
				var cil: String = cile[rng.randi() % cile.size()]
				var k := rng.randf_range(0.8, 1.15) / maxf(Vector3(t[0], t[4], t[8]).length(), 0.01)
				var u := t.duplicate()
				for i in [0, 1, 2, 4, 5, 6, 8, 9, 10]:
					u[i] = float(t[i]) * k
				(r[cil] as Array).append(u)
				n += 1
			else:
				zustava.append(t)
		r[key] = zustava
	print("smrky v udoli nahrazeny listnaci: ", n)


var _vys := {}


## Vyska terenu z mrizky louky (trava_kraj: 2 m, cm v int16) - uz pri stavbe, pred fyzikou.
func _vyska(x: float, z: float) -> float:
	if _vys.is_empty():
		var g: Dictionary = data["trava_kraj"]
		_vys = {"x0": float(g["x0"]), "z0": float(g["z0"]), "k": float(g["k"]), "nx": int(g["nx"]), "nz": int(g["nz"]),
				"y": Marshalls.base64_to_raw(String(g["y"]))}
	var fx := (x - float(_vys["x0"])) / float(_vys["k"])
	var fz := (z - float(_vys["z0"])) / float(_vys["k"])
	var i := clampi(floori(fx), 0, int(_vys["nx"]) - 2)
	var j := clampi(floori(fz), 0, int(_vys["nz"]) - 2)
	fx = clampf(fx - i, 0.0, 1.0)
	fz = clampf(fz - j, 0.0, 1.0)
	var ys: PackedByteArray = _vys["y"]
	var nx: int = _vys["nx"]
	var a := ys.decode_s16((j * nx + i) * 2)
	var b := ys.decode_s16((j * nx + i + 1) * 2)
	var c := ys.decode_s16(((j + 1) * nx + i) * 2)
	var d := ys.decode_s16(((j + 1) * nx + i + 1) * 2)
	return lerpf(lerpf(a, b, fx), lerpf(c, d, fx), fz) / 100.0


func _xf(x: float, y: float, z: float, yaw: float, sc: float, nakl := Vector3.ZERO) -> Array:
	var bs := Basis(Vector3.UP, yaw).rotated(Vector3.RIGHT, nakl.x).rotated(Vector3.FORWARD, nakl.z).scaled(Vector3.ONE * sc)
	return [bs.x.x, bs.y.x, bs.z.x, x, bs.x.y, bs.y.y, bs.z.y, y, bs.x.z, bs.y.z, bs.z.z, z]


## Skalni mesto (radce 09:05): vez nestoji na travniku - u paty sut odpadlych bloku zapadana do zeme, mezi nimi
## kapradi, mech a borůvčí (kerik), v okoli borovice, smrk a briza (les mezi vezemi). Pridava do stavajicich druhu.
func _skalni_mesto() -> void:
	var r: Dictionary = data["rostliny"]
	var need := ["balvan_piskovec_2_0", "kamen_piskovec_1_0", "kamen_piskovec_2_0", "kapradi_1_0", "kapradi_2_0", "kapradi_3_0",
			"mech_1_0", "shrub_02_0", "borovice_0", "smrk_0", "briza_0"]
	for k: String in need:
		if not r.has(k):
			return
	var rng := RandomNumberGenerator.new()
	rng.seed = 7313
	var n := 0
	for key: String in r.keys():
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var ps: PackedScene = load("res://modely/rostliny/%s.glb" % key.trim_suffix("_0"))
		if ps == null:
			continue
		var inst := ps.instantiate()
		var bb := AABB()
		for m in inst.find_children("*", "MeshInstance3D", true, false):
			bb = bb.merge((m as MeshInstance3D).get_aabb())
		inst.free()
		var r0 := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			var c := Vector2(t[3], t[11])
			var rad := r0 * sc
			# sut: 5 bloku a kamenu u paty, zapadane 25-40 %
			for q in 5:
				var a := rng.randf() * TAU
				var d := rad * rng.randf_range(0.85, 1.25)
				var p := c + Vector2(cos(a), sin(a)) * d
				var velky := q == 0
				var s2 := rng.randf_range(0.6, 1.1) if velky else rng.randf_range(0.5, 1.4)
				var kind := "balvan_piskovec_2_0" if velky else ("kamen_piskovec_1_0" if rng.randf() < 0.6 else "kamen_piskovec_2_0")
				(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - s2 * rng.randf_range(0.2, 0.4), p.y, rng.randf() * TAU, s2,
						Vector3(rng.randf_range(-0.3, 0.3), 0, rng.randf_range(-0.3, 0.3))))
				n += 1
			# kapradi, mech a kerik mezi sutí
			for q in 7:
				var a := rng.randf() * TAU
				var p := c + Vector2(cos(a), sin(a)) * rad * rng.randf_range(0.9, 1.6)
				var kind: String = ["kapradi_1_0", "kapradi_2_0", "kapradi_3_0", "kapradi_1_0", "mech_1_0", "mech_1_0", "shrub_02_0"][q]
				var s2 := rng.randf_range(0.04, 0.09) if kind.begins_with("mech") else rng.randf_range(0.7, 1.3)
				(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, s2))
				n += 1
			# les mezi vezemi: jeden strom u kazde veze (borovice, smrk v chladne souteske, briza na svetline)
			var a := rng.randf() * TAU
			var p := c + Vector2(cos(a), sin(a)) * rad * rng.randf_range(1.6, 2.6)
			var u := rng.randf()
			var kind := "borovice_0" if u < 0.5 else ("smrk_0" if u < 0.8 else "briza_0")
			var ref: Array = (r[kind] as Array)[0]
			var s0 := Vector3(ref[0], ref[4], ref[8]).length()
			(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.1, p.y, rng.randf() * TAU, s0 * rng.randf_range(0.8, 1.2)))
			n += 1
	print("skalni mesto: pridano ", n, " kamenu, rostlin a stromu")


## Les neni park (radce 09:05 C): u stromu parezy, spadle vetve, keriky (lesni patro). Kazdy 5. strom pare nebo
## vetve, kazdy 3. kerik (sipek, ker) v okoli; meritka podle prvni instance druhu (tak jak je model navrzeny).
func _lesni_patro() -> void:
	var r: Dictionary = data["rostliny"]
	var drevo := ["tree_stump_01_0", "tree_stump_02_0", "dry_branches_medium_01_0", "dry_branches_medium_01_1", "dry_branches_medium_01_2"]
	var kere := ["shrub_02_0", "sipek_0"]
	for k: String in drevo + kere:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
	var mer := {}
	for k: String in drevo + kere:
		var t: Array = r[k][0]
		mer[k] = Vector3(t[0], t[4], t[8]).length()
	var rng := RandomNumberGenerator.new()
	rng.seed = 404
	var n := 0
	for key: String in r.keys():
		var lesni := false
		for d: String in ["dub_", "buk_", "lipa_", "smrk_", "borovice_", "olse_", "briza_"]:
			if key.begins_with(d) and not key.contains("_daleko"):
				lesni = true
		if not lesni:
			continue
		var i := 0
		for t: Array in (r[key] as Array).duplicate():
			i += 1
			if i % 5 == 0:
				var k: String = drevo[rng.randi() % drevo.size()]
				var a := rng.randf() * TAU
				var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(2.0, 6.0)
				(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.8, 1.3)))
				n += 1
			if i % 3 == 0:
				var k: String = kere[rng.randi() % kere.size()]
				var a := rng.randf() * TAU
				var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(3.0, 7.0)
				(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.7, 1.3)))
				n += 1
	print("lesni patro: pridano ", n, " parezu, vetvi a keru")


## Tvrz zvenci (radce: prvni dojem): u paty hradeb zarostle - koprivy, vysoka trava, pampelisky (kosa tam
## nedosahne); na brehu prikopu vrby hlavate (orezavane, lidska stopa). Obvod hradeb z exportu: x -27..18, z -16..17.
func _tvrz_zvencí() -> void:
	var r: Dictionary = data["rostliny"]
	for k: String in ["nettle_plant_0", "grass_medium_02_0", "dandelion_01_0", "vrba_hlavata_1_0", "vrba_hlavata_2_0"]:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
	var mer := {}
	for k: String in ["nettle_plant_0", "grass_medium_02_0", "dandelion_01_0", "vrba_hlavata_1_0", "vrba_hlavata_2_0"]:
		var t: Array = r[k][0]
		mer[k] = Vector3(t[0], t[4], t[8]).length()
	var voda := float(data.get("voda_y", -2.75))
	var rng := RandomNumberGenerator.new()
	rng.seed = 1390
	var x0 := -27.4
	var x1 := 18.3
	var z0 := -16.4
	var z1 := 17.2
	var obvod := 2.0 * ((x1 - x0) + (z1 - z0))
	var n := 0
	for i in int(obvod * 3.0):
		var u := rng.randf() * obvod
		var off := 0.3 + pow(rng.randf(), 1.5) * 2.2
		var p: Vector2
		if u < x1 - x0:
			p = Vector2(x0 + u, z0 - off)
		elif u < 2.0 * (x1 - x0):
			p = Vector2(x0 + u - (x1 - x0), z1 + off)
		elif u < 2.0 * (x1 - x0) + (z1 - z0):
			p = Vector2(x0 - off, z0 + u - 2.0 * (x1 - x0))
		else:
			p = Vector2(x1 + off, z0 + u - 2.0 * (x1 - x0) - (z1 - z0))
		if absf(p.x + 3.0) < 2.5 and p.y > z1:
			continue                                    # pred branou a mostem volno
		var y := _vyska(p.x, p.y)
		if y < voda + 0.25:
			continue
		var w := rng.randf()
		var k := "nettle_plant_0" if w < 0.4 else ("grass_medium_02_0" if w < 0.85 else "dandelion_01_0")
		(r[k] as Array).append(_xf(p.x, y - 0.03, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.8, 1.3)))
		n += 1
	# vrby hlavate na brehu prikopu: misto tesne nad hladinou na obvodu 4-12 m za hradbou
	var v := 0
	for i in 400:
		if v >= 14:
			break
		var a := rng.randf() * TAU
		var p := Vector2(-4.5, 0.4) + Vector2(cos(a) * 34.0, sin(a) * 28.0) * rng.randf_range(0.95, 1.25)
		var y := _vyska(p.x, p.y)
		if y < voda + 0.15 or y > voda + 1.2 or (absf(p.x + 3.0) < 6.0 and p.y > 0.0):
			continue
		var k := "vrba_hlavata_1_0" if rng.randf() < 0.5 else "vrba_hlavata_2_0"
		(r[k] as Array).append(_xf(p.x, y - 0.1, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.85, 1.15)))
		v += 1
	print("tvrz zvenci: %d rostlin u hradeb, %d vrb u prikopu" % [n, v])


func _plants(parent: Node3D, quality: int) -> void:
	var root := Node3D.new()
	root.name = "Rostliny"
	parent.add_child(root)
	var keep_low: float = [0.3, 0.6, 1.0][quality]
	var keep_tree: float = [0.5, 0.8, 1.0][quality]
	var grass_mat := material("trava_divoka")
	var scenes := {}
	_smrky_na_listnace()
	_skalni_mesto()
	_lesni_patro()
	_tvrz_zvencí()
	# zakladni modely pred vzdalenymi verzemi: vzdalene LOD pak sdili materialy (a textury) zakladniho modelu
	var klice: Array = data["rostliny"].keys()
	klice.sort_custom(func(x: String, y: String) -> bool: return int(x.contains("_daleko")) < int(y.contains("_daleko")))
	var mat_zaklad := {}                 # druh -> {jmeno materialu: Material}
	var imp := {}                        # druh impostoru -> {bunka 256 m: [Color(pata xyz, meritko+otoceni)]}
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
					# listi s pruhlednosti/predpruchodem (briza, smrk): ve stinu se kreslilo jako plny cerny tvar
					# (stinovy pruchod netestuje alfu) - alfa nuzky jako u dubu a lipy
					if om is BaseMaterial3D and (om as BaseMaterial3D).transparency in [BaseMaterial3D.TRANSPARENCY_ALPHA, BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS]:
						(om as BaseMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
						(om as BaseMaterial3D).alpha_scissor_threshold = 0.5
			if kind.begins_with("skala_") and not kind.contains("_daleko2"):
				for nm_: String in md.keys():
					var om_: Material = md[nm_]
					if om_ is BaseMaterial3D and nm_.begins_with("skala") and (om_ as BaseMaterial3D).albedo_texture:
						md[nm_] = _skala_detail(om_ as BaseMaterial3D)
				for i in mesh.get_surface_count():
					var om2 := mesh.surface_get_material(i)
					if om2 and md.has(om2.resource_name):
						mesh.surface_set_material(i, md[om2.resource_name])
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
		# K3: za plnym stromem impostor (pohled z atlasu); jednoduchy tvar jen kdyz impostor pro druh chybi
		var imp_druh := _imp_druh(kind) if tvar != "" else ""
		var tvar_mesh: Mesh = _tvar_mesh(tvar, mesh.get_aabb(), _listi(mesh)) if tvar != "" and imp_druh == "" else null
		var imp_s := mesh.get_aabb().size.y / float(_imp_meta[imp_druh]["vyska"]) if imp_druh != "" else 1.0
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
			# mech u skal byl v exportu zvetseny 25-50x (vyska 0.6-1.6 m misto cm): plachty 30 m ve vzduchu
			if kind.begins_with("mech_") or kind.begins_with("moss_") or kind.begins_with("rock_moss"):
				var sc := xf.basis.get_scale().x
				if sc > 2.0:
					xf.basis = xf.basis.scaled(Vector3.ONE * (randf_range(0.8, 1.6) / sc))
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
			if imp_druh != "":
				mmi.visibility_range_end = STROM_PREP
				mmi.visibility_range_end_margin = 10.0
				mmi.cast_shadow = on
				for xf: Transform3D in list:
					var bc := Vector2i(floori(xf.origin.x / IMP_BUNKA), floori(xf.origin.z / IMP_BUNKA))
					if not imp.has(imp_druh):
						imp[imp_druh] = {}
					if not imp[imp_druh].has(bc):
						imp[imp_druh][bc] = []
					var yaw := fposmod(atan2(-xf.basis.x.z, xf.basis.x.x), TAU)
					var sc := xf.basis.get_scale().y * imp_s
					imp[imp_druh][bc].append(Color(xf.origin.x, xf.origin.y, xf.origin.z, roundf(sc * 256.0) + yaw / TAU * 0.999))
			elif tvar_mesh:
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
				mmi.visibility_range_end = [22.0, 32.0, 45.0][quality]
				mmi.visibility_range_end_margin = 6.0
			elif mid:
				mmi.visibility_range_end = [50.0, 70.0, 95.0][quality]
				mmi.visibility_range_end_margin = 10.0
			else:
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
				mmi.visibility_range_end_margin = 40.0
			root.add_child(mmi)
	_impostory(root, imp)
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
		# modely od Misi (nove._import_sketchup): materialy pojmenovane podle hernich -> stejne fotky jako stavby
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var msh := (mi as MeshInstance3D).mesh
			for i in msh.get_surface_count():
				var om := msh.surface_get_material(i)
				if om and data["materialy"].has(om.resource_name.split(".")[0]):
					(mi as MeshInstance3D).set_surface_override_material(i, material(om.resource_name))
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
			# model z importu (hostinec): kolize jen z puvodni site <id>_kolize, ta se nekresli
			var vse := n.find_children("*", "MeshInstance3D", true, false)
			var kol := vse.filter(func(m: Node) -> bool: return String(m.name).ends_with("_kolize"))
			for mi in vse:
				if kol.is_empty() or mi in kol:
					_trimesh(mi as MeshInstance3D)
				if mi in kol:
					(mi as MeshInstance3D).visible = false
				else:
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
