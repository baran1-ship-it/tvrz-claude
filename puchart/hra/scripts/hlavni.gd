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

func _ready() -> void:
	_prostredi()
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
		mer.zacni(svet, cam)
		mer.konec.connect(_prochazka)
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
	var meri := FileAccess.file_exists("res://data/mereni.json") and (OS.get_environment("PUCHART_MERENI") == "1" or not OS.has_feature("pc"))
	if OS.get_environment("PUCHART_TEST") == "pruchod":
		_test_pruchod.call_deferred()
	elif _foto == "" and not meri:
		_prochazka.call_deferred()
	_kolize_hradu.call_deferred()

## Kolize hradu pro procházku: trojúhelníková kolize ze sítí modelu (zdi, mosty, schody) – jedno statické těleso.
func _kolize_hradu() -> void:
	var h := get_node_or_null("Hrad")
	if h == null or _foto != "":
		return
	# Havran: kolize z kvádrů uzlu KOLIZE (zdi, podlahy, mostovky, schody jako rampy); starší návrhy bez něj ze sítí
	var kol := h.find_children("KOLIZE*", "MeshInstance3D", true, false)
	for mi in (kol if kol.size() > 0 else h.find_children("*", "MeshInstance3D", true, false)):
		(mi as MeshInstance3D).create_trimesh_collision()

func _test_pruchod() -> void:
	await get_tree().create_timer(2.0).timeout   # kolize hradu (deferred) a terén kolem
	var cam: Camera3D = hrac.get_node("Kamera")
	cam.top_level = false; cam.transform = Transform3D(Basis(), Vector3(0, 1.65, 0))
	var t: Node = load("res://scripts/test_pruchod.gd").new(); add_child(t)
	t.zacni(self, hrac)

func _prochazka() -> void:
	var cam: Camera3D = hrac.get_node("Kamera")
	cam.top_level = false; cam.transform = Transform3D(Basis(), Vector3(0, 1.65, 0))
	hrac.set_physics_process(true)
	var pr: CanvasLayer = load("res://scripts/prochazka.gd").new(); add_child(pr)
	pr.zacni(self, hrac)

func _process(_d: float) -> void:
	if _foto == "":
		return
	_snimek += 1
	if _snimek == 40:
		var c := _foto.split(";")
		get_viewport().get_texture().get_image().save_png(c[1])
		print("FOTO ", c[1], " kresleni ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
			" troj ", RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
		get_tree().quit()

func _prostredi() -> void:
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
	# vzdušná perspektiva: hloubková mlha je levná a v Compatibility funguje (žádná objemová mlha)
	env.fog_enabled = true
	env.fog_light_color = Color(0.68, 0.75, 0.84)
	env.fog_density = 0.00018
	env.fog_aerial_perspective = 0.6
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new(); we.environment = env
	add_child(we)
