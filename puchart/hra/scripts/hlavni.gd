extends Node3D
## Hlavní scéna: svět, světlo, obloha, hráč, panel měření. Vše kódem – žádné ručně psané .tscn s vymyšlenými uid
## (pravidlo Havrana 28. 10.).
## Snímek bez hráče: PUCHART_FOTO="x,z,vyska_nad_terenem,cil_x,cil_z,cil_vyska;soubor.png" (y dopočte z terénu).

const Svet := preload("res://scripts/svet.gd")
const Hrac := preload("res://scripts/hrac.gd")
const Diag := preload("res://scripts/diag.gd")
const Les := preload("res://scripts/les.gd")

var svet: Node3D
var hrac: CharacterBody3D
var _foto := ""
var _snimek := 0
var _mereni: Array = []
var _env: Environment
var _fog_zakl: Array = []
var _les := 0.0       # 0..1 zápoj korun kolem hráče (mlha v lese – Havran daylight.gd _les_mlha)
var _uvnitr := 0.0    # 0 venku, 1 pod střechou/klenbou (méně modrého světla z oblohy – Havran _amb)

func _ready() -> void:
	# herní data mimo APK (scripts/data.gd, Havran): první spuštění je stáhne, další jen načtou
	if not ResourceLoader.exists("res://modely/hrady/puchart.glb"):
		var vrstva := CanvasLayer.new(); add_child(vrstva)
		var pozadi := ColorRect.new(); pozadi.color = Color(0.1, 0.09, 0.08); pozadi.set_anchors_preset(Control.PRESET_FULL_RECT); vrstva.add_child(pozadi)
		var txt := Label.new(); txt.set_anchors_preset(Control.PRESET_FULL_RECT)
		txt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; txt.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		txt.add_theme_font_size_override("font_size", 36); txt.text = "Připravuji herní data…"; vrstva.add_child(txt)
		var dat: Node = load("res://scripts/data.gd").new(); add_child(dat)
		dat.status.connect(func(t: String) -> void: txt.text = t)
		if not await dat.ensure():
			return   # hláška zůstane na obrazovce (internet / znovu spustit)
		vrstva.queue_free()
	_start()

func _start() -> void:
	_prostredi()
	if FileAccess.file_exists("res://data/rozpocty.json"):   # rozlišení 3D (rozpocty.json obraz_3d)
		var o: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json")).get("obraz_3d", {})
		get_viewport().scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
		get_viewport().scaling_3d_scale = float(o.get("scale", 1.0))
	svet = Svet.new(); svet.name = "Svet"
	add_child(svet)
	var hrad_id := OS.get_environment("PUCHART_HRAD")
	if hrad_id == "":
		hrad_id = "puchart"
	if FileAccess.file_exists("res://modely/hrady/%s.glb" % hrad_id) or ResourceLoader.exists("res://modely/hrady/%s.glb" % hrad_id):
		var h: Node3D = load("res://modely/hrady/%s.glb" % hrad_id).instantiate()
		h.name = "Hrad"
		add_child(h)
		for k in h.find_children("KOLIZE*", "MeshInstance3D", true, false):
			(k as MeshInstance3D).visible = false
		_svetla(h)
	if ResourceLoader.exists("res://modely/hrady/skaly.glb"):   # skalní výchozy (blender/skaly.py, skaly.json)
		var sk: Node3D = load("res://modely/hrady/skaly.glb").instantiate(); sk.name = "Skaly"; add_child(sk)
		for k in sk.find_children("KOLIZE*", "MeshInstance3D", true, false):
			(k as MeshInstance3D).visible = false
	var _jp_dosah := 220.0
	if FileAccess.file_exists("res://data/voda_hra.json"):
		_jp_dosah = float(JSON.parse_string(FileAccess.get_file_as_string("res://data/voda_hra.json"))["koryto"]["jemny_pas"]["dosah_kresleni_m"])
	if ResourceLoader.exists("res://modely/voda.glb"):   # potoky a lávky (blender/voda.py, voda_hra.json)
		var vo: Node3D = load("res://modely/voda.glb").instantiate(); vo.name = "Voda"; add_child(vo)
		var mv := ShaderMaterial.new(); mv.shader = load("res://shaders/voda.gdshader")
		for mi in vo.find_children("*", "MeshInstance3D", true, false):
			var m := mi as MeshInstance3D
			if m.name.begins_with("KOLIZE"): m.visible = false; continue
			if m.name.begins_with("BREH"):   # jemný pás břehů: materiál terénu, jen nablízko (dál ho nahradí dlaždice)
				m.material_override = svet.mat_zem; m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				m.visibility_range_end = _jp_dosah; continue
			for i in m.mesh.get_surface_count():
				var mt := m.mesh.surface_get_material(i)
				if mt != null and mt.resource_name.begins_with("voda"):
					m.set_surface_override_material(i, mv); m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var les := Les.new(); les.name = "Les"
	add_child(les)
	les.postav(svet)
	hrac = Hrac.new(); hrac.name = "Hrac"
	var tvar := CollisionShape3D.new(); var kap := CapsuleShape3D.new(); kap.radius = 0.3; kap.height = 1.75
	tvar.shape = kap; tvar.position.y = 0.875; hrac.add_child(tvar)
	var cam := Camera3D.new(); cam.name = "Kamera"; cam.position.y = 1.65; cam.fov = 70.0; cam.far = 12000.0; cam.near = 0.1
	hrac.add_child(cam)
	add_child(hrac)
	svet.hrac = hrac
	# start: louka nad předním hradem, pohled k ostrohu (hra: přední hrad = počátek)
	var start := Vector3(-60.0, 0.0, -150.0)
	start.y = svet.vyska(start.x, start.z) + 0.2
	hrac.position = start
	hrac.look_at(Vector3(0.0, svet.vyska(0.0, 0.0) + 1.6, 0.0), Vector3.UP)
	hrac.rotation.x = 0.0
	add_child(Diag.new())
	if FileAccess.file_exists("res://data/mereni.json") and (OS.get_environment("PUCHART_MERENI") == "1" or not OS.has_feature("pc")):
		var Mer := load("res://scripts/mereni.gd")
		var mer: Node = Mer.new(); add_child(mer)
		hrac.set_physics_process(false)
		cam.top_level = true
		mer.konec.connect(_prochazka)
		_mereni = [mer, cam]
	_foto = OS.get_environment("PUCHART_FOTO")
	var byl: Node3D = load("res://scripts/byliny.gd").new(); byl.name = "Byliny"; add_child(byl)
	if _foto != "":
		var c := _foto.split(";")
		var v := c[0].split_floats(",")
		var p := Vector3(v[0], svet.vyska(v[0], v[1]) + v[2], v[1])
		var t := Vector3(v[3], svet.vyska(v[3], v[4]) + v[5], v[4])
		hrac.set_physics_process(false)
		hrac.position = p - Vector3(0, 1.65, 0)
		cam.look_at_from_position(p, t, Vector3.UP)
		cam.top_level = true
		if OS.get_environment("PUCHART_ORTO") != "":   # půdorys shora: pravoúhlá projekce, velikost = výška záběru v m
			cam.projection = Camera3D.PROJECTION_ORTHOGONAL
			cam.size = float(OS.get_environment("PUCHART_ORTO"))
	byl.postav(svet, cam)
	var ker: Node3D = load("res://scripts/byliny.gd").new(); ker.name = "Kere"; add_child(ker)   # keře a zmlazení (data/kere.json)
	ker.postav(svet, cam, "res://data/kere.json")
	if _foto == "" and OS.get_environment("PUCHART_TEST") == "" and _pr.get("predehrati", {}).get("zapojeno", false):   # shadery všech materiálů sestavit hned, ne až za chůze (záseky při 1. průchodu – Havran 0.62)
		await get_tree().process_frame
		await load("res://scripts/predehrati.gd").predehrej(self, cam, byl.vsechny_site() + ker.vsechny_site(), int(_pr.get("predehrati", {}).get("snimku", 4)))
	if _mereni.size() > 0: _mereni[0].zacni(svet, _mereni[1])
	var meri := FileAccess.file_exists("res://data/mereni.json") and (OS.get_environment("PUCHART_MERENI") == "1" or not OS.has_feature("pc"))
	if OS.get_environment("PUCHART_TEST") == "pruchod":
		_test_pruchod.call_deferred()
	elif OS.get_environment("PUCHART_TEST") == "sceny":
		_test_sceny.call_deferred()
	elif _foto == "" and not meri:
		_prochazka.call_deferred()
	_kolize_hradu.call_deferred()
	for jm in OS.get_environment("PUCHART_SKRYJ").split(",", false):   # diagnostika výkonu: skrýt vrstvu (Les, Kere, Byliny, Hrad, Skaly, Voda)
		var n := get_node_or_null(jm)
		if n: n.visible = false

## Kolize hradu pro procházku: trojúhelníková kolize ze sítí modelu (zdi, mosty, schody) – jedno statické těleso.
func _kolize_hradu() -> void:
	if _foto != "":
		return
	for jm in ["Hrad", "Skaly", "Voda"]:
		var h := get_node_or_null(jm)
		if h != null: _kolize_uzlu(h)

func _kolize_uzlu(h: Node) -> void:
	# Havran: kolize z kvádrů uzlu KOLIZE (zdi, podlahy, mostovky, schody jako rampy); starší návrhy bez něj ze sítí
	var kol := h.find_children("KOLIZE*", "MeshInstance3D", true, false)
	for mi in (kol if kol.size() > 0 else h.find_children("*", "MeshInstance3D", true, false)):
		(mi as MeshInstance3D).create_trimesh_collision()
		for cs in (mi as MeshInstance3D).find_children("*", "CollisionShape3D", true, false):   # oboustranně: úlomky suti a stupně skal mají
			if h.name != "Hrad" and (cs as CollisionShape3D).shape is ConcavePolygonShape3D:   # hrad = uzavřené kvádry   # stěny s obráceným pořadím vrcholů – zvenku se jimi procházelo (povrch_kolize)
				((cs as CollisionShape3D).shape as ConcavePolygonShape3D).backface_collision = true

## Pochodně ve věžích, hladomorně a sklepě (data/svetla.json ze stavitele hradu): bez stínů, zhasínají na dálku.
func _svetla(h: Node3D) -> void:
	if not FileAccess.file_exists("res://data/svetla.json"):
		return
	for s in JSON.parse_string(FileAccess.get_file_as_string("res://data/svetla.json"))["svetla"]:
		var l := OmniLight3D.new(); var p: Array = s["pos"]
		l.position = Vector3(p[0], p[1], p[2]); l.light_color = Color(1.0, 0.68, 0.38)
		l.light_energy = s["energie"]; l.omni_range = s["dosah"]; l.shadow_enabled = false
		l.distance_fade_enabled = true; l.distance_fade_begin = 35.0; l.distance_fade_length = 10.0
		h.add_child(l)

func _test_pruchod() -> void:
	await get_tree().create_timer(2.0).timeout   # kolize hradu (deferred) a terén kolem
	var cam: Camera3D = hrac.get_node("Kamera")
	cam.top_level = false; cam.transform = Transform3D(Basis(), Vector3(0, 1.65, 0))
	var t: Node = load("res://scripts/test_pruchod.gd").new(); add_child(t)
	t.zacni(self, hrac)

func _test_sceny() -> void:
	await get_tree().create_timer(1.0).timeout
	var t: Node = load("res://scripts/test_sceny.gd").new(); add_child(t)
	t.zacni(self, hrac.get_node("Kamera"))

func _prochazka() -> void:
	var cam: Camera3D = hrac.get_node("Kamera")
	cam.top_level = false; cam.transform = Transform3D(Basis(), Vector3(0, 1.65, 0))
	hrac.set_physics_process(true)
	var pr: CanvasLayer = load("res://scripts/prochazka.gd").new(); add_child(pr)
	pr.zacni(self, hrac)

func _atmosfera(d: float) -> void:
	if _env == null or hrac == null: return
	var cam: Camera3D = get_viewport().get_camera_3d()
	if cam == null: return
	var p := cam.global_position
	var lm: Dictionary = _pr.get("atmosfera", {}).get("les_mlha", {}); var it: Dictionary = _pr.get("atmosfera", {}).get("interier", {})
	if Engine.get_process_frames() % 10 == 0:
		var les: Node = get_node_or_null("Les")
		_les_cil = les.zapoj(p.x, p.z, lm) if les and les.has_method("zapoj") and not lm.is_empty() else 0.0
		var q := PhysicsRayQueryParameters3D.create(p, p + Vector3.UP * float(it.get("paprsek_nahoru_m", 25.0)))
		_uvnitr_cil = 1.0 if not it.is_empty() and get_world_3d().direct_space_state.intersect_ray(q).size() > 0 else 0.0
	_les = move_toward(_les, _les_cil, d * float(lm.get("rychlost", 0.5))); _uvnitr = move_toward(_uvnitr, _uvnitr_cil, d * float(it.get("rychlost", 1.5)))
	var hloubkova := _sceny(d, cam) > 0.0
	if not lm.is_empty():
		var lb: Array = lm["barva"]
		_env.fog_light_color = (_fog_zakl[0] as Color).lerp(Color(lb[0], lb[1], lb[2]), _les * float(lm["podil_barvy"]))
		_env.fog_density = 1.0 if hloubkova else lerpf(_fog_zakl[1], float(lm["hustota_max"]), _les)
	else:
		_env.fog_density = 1.0 if hloubkova else _fog_zakl[1]
	_env.fog_sky_affect = clampf(0.35 * (1.0 - _kresleni / 12000.0) * 1.5, 0.0, 0.35)   # obloha do oparu podle zkrácení kreslení (plynule)
	if not it.is_empty():
		var ab: Array = it["ambient_barva"]; var ub := float(it["ubytek_oblohy"])
		var ve: Dictionary = _pr["atmosfera"].get("venku", {})   # venku: část okolního světla odraz od země a zdí (teplý), ne jen modrá obloha
		var vb: Array = ve.get("barva", ab); var vo := float(ve.get("podil_oblohy", 1.0))
		_env.ambient_light_energy = lerpf(float(ve.get("ambient", it["ambient"])), float(it["ambient"]), _uvnitr) * (1.0 - _uvnitr * ub)
		_env.ambient_light_sky_contribution = lerpf(vo, 1.0, _uvnitr) * (1.0 - _uvnitr * ub)
		_env.ambient_light_color = Color(vb[0], vb[1], vb[2]).lerp(Color(ab[0], ab[1], ab[2]), _uvnitr)
		_env.tonemap_exposure = 1.0 + _uvnitr * float(it["expozice_navic"])

var _les_cil := 0.0
var _uvnitr_cil := 0.0
var _dh: Dictionary = {}        # data/dohled.json (nastroje/viditelnost.py: dohled na mřížce × směry)
var _dh_data := PackedByteArray()
var _sc_pr: Dictionary = {}     # data/sceny_pravidla.json hra
var _kresleni := 12000.0        # aktuální vzdálenost kreslení kamery (plynule)
var _kresleni_cil := 12000.0
var scena_typ := ""
var _sc_prvni := false             # pro diag a hlídač scén

## Scény (GPT „Inteligentní tvorba scén“ bod 4–6): podle nejbližšího bodu trasy typ A/B/C a skutečný dohled z DMR+lesa.
## Kamera kreslí jen do dohledu × násobek, mlha je na konci kreslení skoro neprůhledná – nic neodskočí; panorama C plné.
func _sceny(d: float, cam: Camera3D) -> float:
	if _sc_pr.is_empty():
		if not (FileAccess.file_exists("res://data/dohled.json") and FileAccess.file_exists("res://data/sceny_pravidla.json")): return 0.0
		_sc_pr = JSON.parse_string(FileAccess.get_file_as_string("res://data/sceny_pravidla.json"))
		_dh = JSON.parse_string(FileAccess.get_file_as_string("res://data/dohled.json"))
		_dh_data = FileAccess.get_file_as_bytes("res://data/dohled.bin")
	var hr: Dictionary = _sc_pr["hra"]; var ty_pr: Dictionary = _sc_pr["typy"]
	var p := cam.global_position
	if Engine.get_process_frames() % 6 == 0 or OS.get_environment("PUCHART_TEST") == "sceny":   # test: každý snímek (QA: typ z předchozího bodu)
		# dohled v zorném poli: 3 sektory kolem směru pohledu, maximum ze 4 okolních bodů mřížky (nic nezmizí dřív)
		var f := -cam.global_basis.z; var ns: int = _dh["smeru"]
		var uhel := fposmod(atan2(f.x, -f.z), TAU); var si := int(round(uhel / TAU * ns)) % ns
		var gx := (p.x - float(_dh["x0"])) / float(_dh["krok_m"]); var gz := (p.z - float(_dh["z0"])) / float(_dh["krok_m"])
		var dohled := 0.0   # bilineárně mezi body mřížky, maximum ze 3 sektorů zorného pole
		var ix0 := clampi(int(gx), 0, int(_dh["nx"]) - 2); var iz0 := clampi(int(gz), 0, int(_dh["nz"]) - 2)
		var fx := clampf(gx - ix0, 0.0, 1.0); var fz := clampf(gz - iz0, 0.0, 1.0)
		for k in [-1, 0, 1]:
			var sk: int = (si + int(k) + ns) % ns; var v := [0.0, 0.0, 0.0, 0.0]
			for q in 4:
				var i: int = (((iz0 + q / 2) * int(_dh["nx"]) + ix0 + q % 2) * ns + sk) * 2
				v[q] = float(_dh_data.decode_u16(i))
			dohled = maxf(dohled, lerpf(lerpf(v[0], v[1], fx), lerpf(v[2], v[3], fx), fz))
		var nad: float = p.y - svet.vyska(p.x, p.z)
		var typ := "C" if (dohled >= float(ty_pr["panorama_od_m"]) or nad > float(hr["let_nad_m"])) else ("A" if dohled < float(ty_pr["uzavrena_do_m"]) else "B")
		var ty: Dictionary = hr["typy"][typ]
		_kresleni_cil = clampf(dohled * float(hr["nasobek_dohledu"]), float(ty["kresleni_min_m"]), float(ty["kresleni_max_m"]))
		scena_typ = typ
	# hystereze: dohled se otevírá rychle (nic nesmí chybět), zavírá pomalu (žádné pumpování mlhy při otáčení)
	var rych: float = float(hr["rychlost_m_s"]) * (4.0 if _kresleni_cil > _kresleni else 1.0)
	# první vyhodnocení a test scén: hned na cíl (dřív start na 12 km a zavírání 60 m/s = 3 min kreslení celé krajiny)
	if _foto != "" or not _sc_prvni: _kresleni = _kresleni_cil; _sc_prvni = true
	else: _kresleni = move_toward(_kresleni, _kresleni_cil, d * rych)
	cam.far = _kresleni + 50.0
	# hloubková mlha vždy (dřív přepínání exponenciální ↔ hloubková = skok obrazu na hranici scén, hlídač scén 2. 11.):
	# čistý obraz do mlha_od × kreslení, na konci kreslení plně zakryto; panorama (12 km) = mlha jen u obzoru
	_env.fog_mode = Environment.FOG_MODE_DEPTH
	_env.fog_depth_begin = _kresleni * float(_sc_pr["hra"]["mlha_od"]); _env.fog_depth_end = _kresleni; _env.fog_depth_curve = float(_sc_pr["hra"]["mlha_krivka"])
	return 1.0

func _process(_d: float) -> void:
	_atmosfera(_d)
	if _foto == "":
		return
	_snimek += 1
	if _snimek == 40:
		var c := _foto.split(";")
		get_viewport().get_texture().get_image().save_png(c[1])
		print("FOTO ", c[1], " kresleni ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			" troj ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
		get_tree().quit()

var _pr: Dictionary = {}

func _prostredi() -> void:
	if FileAccess.file_exists("res://data/prostredi.json"):
		_pr = JSON.parse_string(FileAccess.get_file_as_string("res://data/prostredi.json"))
	# léto 1393, odpoledne; slunce z JZ (PDF: hotová letní krajina). Stín jen blízko (rozpocty.json stiny).
	var slunce := DirectionalLight3D.new()
	slunce.rotation_degrees = Vector3(-38.0, -140.0, 0.0)
	slunce.light_energy = 1.0
	slunce.light_color = Color(1.0, 0.95, 0.86)
	slunce.shadow_enabled = true
	slunce.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	slunce.directional_shadow_max_distance = 40.0
	add_child(slunce)
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.32, 0.5, 0.78)
	sky_mat.sky_horizon_color = Color(0.72, 0.78, 0.84)
	sky_mat.ground_horizon_color = Color(0.6, 0.64, 0.62)
	sky_mat.ground_bottom_color = Color(0.25, 0.27, 0.22)
	sky_mat.sun_angle_max = 20.0
	var sky := Sky.new(); sky.sky_material = sky_mat
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.tonemap_white = 1.6
	# atmosféra z dat (pravidla/svet/prostredi.json atmosfera – Havran daylight.gd, GPT výzkum: hloubková/výšková mlha)
	var at: Dictionary = _pr.get("atmosfera", {})
	var c3 := func(a: Array) -> Color: return Color(a[0], a[1], a[2])
	env.fog_enabled = true
	env.fog_light_color = c3.call(at.get("mlha_barva", [0.68, 0.75, 0.84]))
	env.fog_density = float(at.get("mlha_hustota", 0.0005))
	env.fog_aerial_perspective = float(at.get("vzdusna_perspektiva", 0.75))
	env.fog_sky_affect = 0.0
	env.fog_sun_scatter = float(at.get("rozptyl_slunce", 0.0))
	if at.has("prizemni_mlha"):
		env.fog_height = float(at["prizemni_mlha"]["vyska_y"]); env.fog_height_density = float(at["prizemni_mlha"]["hustota"])
	if at.has("zare"):
		env.glow_enabled = true; env.glow_intensity = float(at["zare"]["intenzita"]); env.glow_bloom = float(at["zare"]["bloom"]); env.glow_hdr_threshold = float(at["zare"]["prah_hdr"])
	if at.has("uprava"):
		env.adjustment_enabled = true; env.adjustment_contrast = float(at["uprava"]["kontrast"]); env.adjustment_saturation = float(at["uprava"]["sytost"])
	_env = env; _fog_zakl = [env.fog_light_color, env.fog_density]
	var we := WorldEnvironment.new(); we.environment = env
	add_child(we)
