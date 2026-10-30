extends Node3D
## Les 1393: stromy z hra/data/stromy.bin (polohy a výšky ze skutečných korun DMP 1G − DMR 5G, druh podle
## historie_vegetace.json – nastroje/stanoviste_realne.py). Modely Havrana (stromy_modely.json).
## Blízko: plné modely v buňkách (MultiMesh na buňku a variantu, auto-LOD importu podle vzdálenosti buňky).
## Dál: zkřížené karty *_daleko (6 troj.) v jednom MultiMesh na variantu.
## Přechod per pixel ditheringem podle vzdálenosti (StandardMaterial distance_fade) – strom se nekreslí dvakrát
## a nic nebliká (Compatibility nemá průhledný fade visibility range – PDF kap. 9).

var svet: Node3D
var cfg: Dictionary

func postav(s: Node3D) -> void:
	svet = s
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/stromy_modely.json"))
	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/stromy.json"))
	var raw := FileAccess.get_file_as_bytes("res://data/stromy.bin").to_float32_array()
	var dreviny: Array = info["dreviny"]
	var bl: float = cfg["blizko_m"]; var pr: float = cfg["prechod_m"]; var B: float = cfg["bunka_m"]
	var l0: float = cfg["lod0_m"]
	# snímky návrhů: PUCHART_STROMY_BLIZKO=m (karty až dál – vypadají jako krabice do ~80 m; dluh: impostory, krok D)
	if OS.get_environment("PUCHART_STROMY_BLIZKO") != "":
		bl = float(OS.get_environment("PUCHART_STROMY_BLIZKO"))
	var mer: Array = cfg["meritko"]
	# varianta -> seznam transformací
	var skupiny := {}
	var vynech: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/hrady_bez_stromu.json"))["obdelniky"] if FileAccess.file_exists("res://data/hrady_bez_stromu.json") else []
	for i in range(0, raw.size(), 5):
		var x := raw[i]; var z := raw[i + 1]; var h := raw[i + 2]
		var ven := false
		for o in vynech:
			if x > o[0] and x < o[2] and z > o[1] and z < o[3]:
				ven = true
		if ven:
			continue
		var dr: String = dreviny[int(raw[i + 3])]
		var model: String = cfg["dreviny"][dr]["model"]
		var var_h: Dictionary = cfg["varianty"][model]
		var nej := ""; var nej_d := 1e9
		for v in var_h:
			var d := absf(float(var_h[v]) - h)
			if d < nej_d: nej_d = d; nej = v
		var sc := clampf(h / float(var_h[nej]), mer[0], mer[1])
		var t := Transform3D(Basis(Vector3.UP, raw[i + 4]).scaled(Vector3(sc, sc * randf_range(0.95, 1.05), sc)),
			Vector3(x, svet.vyska(x, z) - 0.15 * sc, z))
		var k := "%s_%s" % [model, nej]
		if not skupiny.has(k): skupiny[k] = []
		skupiny[k].append(t)
	var imp_meta: Dictionary = {}
	if FileAccess.file_exists("res://textury/impostory/impostory.json"):
		imp_meta = JSON.parse_string(FileAccess.get_file_as_string("res://textury/impostory/impostory.json"))
	var imp := {}   # druh -> buňka -> [Color(pata x, y, z, round(měřítko*256) + otočení/2π)]
	for k in skupiny:
		var druh: String = k.split("_")[0]
		if imp_meta.has(druh) and ResourceLoader.exists("res://textury/impostory/%s_a.png" % druh):
			var V: float = imp_meta[druh]["vyska"]
			for t: Transform3D in skupiny[k]:
				var h := float(cfg["varianty"][druh][k.substr(druh.length() + 1)]) * t.basis.get_scale().y
				var rot := fposmod(atan2(t.basis.x.z, t.basis.x.x) * -1.0, TAU)
				var bc := Vector2i(floori(t.origin.x / IMP_B), floori(t.origin.z / IMP_B))
				if not imp.has(druh): imp[druh] = {}
				if not imp[druh].has(bc): imp[druh][bc] = []
				imp[druh][bc].append(Color(t.origin.x, t.origin.y, t.origin.z, round(h / V * 256.0) + rot / TAU * 0.999))
		else:
			_daleko(k, skupiny[k], bl, pr)
		_blizko(k, skupiny[k], bl, pr, B, l0)
	_impostory(imp, imp_meta, bl, pr)

const IMP_B := 256.0   # buňka impostorů (Havran: málo volání kreslení, custom data v půl přesnosti -> pozice vůči středu buňky)

## Impostory (převzato z Havrana svet.gd _impostory): jeden čtverec na strom, pohled z atlasu 8×8 podle směru ke kameře.
func _impostory(imp: Dictionary, meta: Dictionary, bl: float, pr: float) -> void:
	var quad := ArrayMesh.new()
	var a := []; a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-1, 0, 0), Vector3(1, 0, 0), Vector3(1, 2, 0), Vector3(-1, 2, 0)])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	quad.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	var n := 0
	for d: String in imp:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/impostor.gdshader")
		m.set_shader_parameter("barva", load("res://textury/impostory/%s_a.png" % d))
		m.set_shader_parameter("normaly", load("res://textury/impostory/%s_n.png" % d))
		var st: Array = meta[d]["stred"]
		m.set_shader_parameter("stred", Vector3(st[0], st[1], st[2]))
		m.set_shader_parameter("polomer", float(meta[d]["polomer"]))
		m.set_shader_parameter("fade_od", bl - 8.0)   # náběh 10 m přes dithering plného stromu (bl - pr .. bl)
		m.set_shader_parameter("fade_do", 1600.0)
		for bc: Vector2i in imp[d]:
			var list: Array = imp[d][bc]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			mm.mesh = quad
			mm.instance_count = list.size()
			var o := Vector3((bc.x + 0.5) * IMP_B, 0.0, (bc.y + 0.5) * IMP_B)
			var lo := Vector3(INF, INF, INF); var hi := -lo
			for i in list.size():
				var c: Color = list[i]
				c = Color(c.r - o.x, c.g, c.b - o.z, c.a)
				mm.set_instance_transform(i, Transform3D.IDENTITY)
				mm.set_instance_custom_data(i, c)
				lo = lo.min(Vector3(c.r, c.g, c.b)); hi = hi.max(Vector3(c.r, c.g, c.b))
			var r := float(meta[d]["polomer"]) * 3.0
			mm.custom_aabb = AABB(lo - Vector3(r, r, r), hi - lo + Vector3(r, r, r) * 2.0)
			var mi := MultiMeshInstance3D.new()
			mi.multimesh = mm; mi.material_override = m
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.position = o
			add_child(mi)
			n += list.size()
	print("impostory: %d stromů" % n)

func _mesh(cesta: String) -> Mesh:
	var sc: Node = load(cesta).instantiate()
	var mi: MeshInstance3D = sc.find_children("*", "MeshInstance3D", true, false)[0]
	var m: Mesh = mi.mesh
	sc.free()
	return m

func _fade(m: Mesh, od: float, do_: float) -> Mesh:
	# kopie materiálů s distance fade (od < do = objevuje se s dálkou, od > do = mizí)
	var mm: Mesh = m.duplicate()
	for s in mm.get_surface_count():
		var mat := mm.surface_get_material(s)
		if mat is BaseMaterial3D:
			var c: BaseMaterial3D = mat.duplicate()
			c.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_DITHER
			c.distance_fade_min_distance = od
			c.distance_fade_max_distance = do_
			mm.surface_set_material(s, c)
	return mm

func _daleko(k: String, ts: Array, bl: float, pr: float) -> void:
	var m := _fade(_mesh("res://modely/stromy/%s_daleko.glb" % k), bl - pr, bl)
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = m
	mm.instance_count = ts.size()
	for i in ts.size(): mm.set_instance_transform(i, ts[i])
	var mi := MultiMeshInstance3D.new(); mi.multimesh = mm; mi.name = "daleko_" + k
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)

func _blizko(k: String, ts: Array, bl: float, pr: float, B: float, l0: float) -> void:
	# staré stromy (25–30 k troj.) i zblízka jako LOD1 – výkon i velikost APK (stare_lod1, docs/ab_srovnani.md)
	var stare_lod1 := k.ends_with("_stary") or k.ends_with("_stara")
	var m0 := _mesh("res://modely/stromy/%s.glb" % (k + "_lod1" if stare_lod1 else k))
	if stare_lod1:
		m0 = m0.duplicate()
	# LOD1 je importovaný bez textur (embedded_image_handling = Discard) – materiály z LOD0, ať nejsou v VRAM dvakrát
	if stare_lod1:
		var vzor: Mesh = _mesh("res://modely/stromy/%s.glb" % (k.split("_")[0] + "_stredni"))
		for s in mini(m0.get_surface_count(), vzor.get_surface_count()):
			m0.surface_set_material(s, vzor.surface_get_material(s))
	var m1raw: Mesh = _mesh("res://modely/stromy/%s_lod1.glb" % k).duplicate()
	for s in mini(m1raw.get_surface_count(), m0.get_surface_count()):
		m1raw.surface_set_material(s, m0.surface_get_material(s))
	var m1 := _fade(m1raw, bl, bl - pr)
	var bunky := {}
	for t in ts:
		var c := Vector2i(floori(t.origin.x / B), floori(t.origin.z / B))
		if not bunky.has(c): bunky[c] = []
		bunky[c].append(t)
	for c in bunky:
		var a: Array = bunky[c]
		# LOD0: buňky se středem do l0 (tvrdě, s hysterezí); LOD1: od l0 do bl + půl úhlopříčky, na konci dithering
		for lod in 2:
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = m0 if lod == 0 else m1
			mm.instance_count = a.size()
			for i in a.size(): mm.set_instance_transform(i, a[i])
			var mi := MultiMeshInstance3D.new(); mi.multimesh = mm
			mi.visibility_range_begin = 0.0 if lod == 0 else l0
			mi.visibility_range_end = l0 if lod == 0 else bl + B * 0.75
			mi.visibility_range_begin_margin = 4.0
			mi.visibility_range_end_margin = 4.0
			mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			if lod == 1:
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			add_child(mi)
