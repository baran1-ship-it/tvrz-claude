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
	var mer: Array = cfg["meritko"]
	# varianta -> seznam transformací
	var skupiny := {}
	for i in range(0, raw.size(), 5):
		var x := raw[i]; var z := raw[i + 1]; var h := raw[i + 2]
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
	for k in skupiny:
		_daleko(k, skupiny[k], bl, pr)
		_blizko(k, skupiny[k], bl, pr, B, l0)

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
	var m0 := _mesh("res://modely/stromy/%s.glb" % k)
	# LOD1 je importovaný bez textur (embedded_image_handling = Discard) – materiály z LOD0, ať nejsou v VRAM dvakrát
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
