extends Node3D
## Test postav v Godotu: herní světlo (slunce 30°, obloha), tři hrdinové, snímek do user://.
const SKLADA := preload("res://nastroje/godot/postava_sklada.gd")
var _snimky := []
var _frame := 0

func _ready() -> void:
	var env := Environment.new()
	var sky := Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.28, 0.45, 0.85); sm.sky_horizon_color = Color(0.75, 0.78, 0.8)
	sm.ground_bottom_color = Color(0.25, 0.22, 0.18); sm.ground_horizon_color = Color(0.6, 0.6, 0.55)
	sky.sky_material = sm; env.sky = sky; env.background_mode = Environment.BG_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_ACES; env.tonemap_white = 1.6
	var we := WorldEnvironment.new(); we.environment = env; add_child(we)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-30, 35, 0); sun.light_energy = 1.3
	sun.light_color = Color(1.0, 0.95, 0.88); sun.shadow_enabled = true; add_child(sun)
	var zem := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(30, 30); zem.mesh = pm
	var zm := StandardMaterial3D.new(); zm.albedo_color = Color(0.32, 0.4, 0.2); zm.roughness = 1.0; zem.material_override = zm; add_child(zem)
	var anims: Array[AnimationLibrary] = [load("res://modely/postavy/animace_ual/UAL1_Standard.glb"), load("res://modely/postavy/animace_ual/UAL2_Standard.glb"), load("res://modely/postavy/animace_ual/postavy_idle.glb")]
	var jm: Array = OS.get_environment("POSTAVY").split(",") if OS.get_environment("POSTAVY") != "" else ["muz", "zena", "kluk"]
	var slozka := OS.get_environment("SLOZKA") if OS.get_environment("SLOZKA") != "" else "res://modely/postavy/hrdinove"
	var n := jm.size()
	var anim := OS.get_environment("ANIM") if OS.get_environment("ANIM") != "" else "Idle"
	for i in n:
		var p := Node3D.new(); p.set_script(SKLADA)
		p.set("slozka", slozka); p.set("postava", jm[i]); p.set("animace", anims); p.set("nazvy_knihoven", PackedStringArray(["ual1", "ual2", "idle"]))
		var a_i: String = anim if anim != "VOLNE" else ["Idle_Volne_1", "Idle_Volne_2", "Idle_Volne_3"][i % 3]
		p.set("vychozi_animace", a_i)
		p.position = Vector3((i - (n - 1) / 2.0) * 0.85, 0, 0)
		add_child(p)
		for k in OS.get_environment("SVLEC").split(",", false):
			p.call("svlekni", k)
	var cam := Camera3D.new(); add_child(cam)
	var close := OS.get_environment("CLOSE") != ""
	if OS.get_environment("CAM") != "":
		var c := OS.get_environment("CAM").split_floats(",")
		cam.position = Vector3(c[0], c[1], c[2]); cam.fov = c[6] if c.size() > 6 else 35.0
		cam.look_at(Vector3(c[3], c[4], c[5]))
	elif close:
		cam.position = Vector3(0, 1.68, 1.6); cam.fov = 30
		cam.look_at(Vector3(0, 1.62, 0))
	else:
		cam.position = Vector3(0, 1.1, 1.6 + 1.0 * n); cam.fov = 40
		cam.look_at(Vector3(0, 0.95, 0))

func _process(_dt: float) -> void:
	_frame += 1
	if OS.get_environment("MRK") != "" and _frame == 30:
		_zavri(self)
	if _frame == int(OS.get_environment("FR")) if OS.get_environment("FR") != "" else _frame == 40:
		var img := get_viewport().get_texture().get_image()
		var out := OS.get_environment("OUT") if OS.get_environment("OUT") != "" else "/tmp/godot_snimek.png"
		img.save_png(out); print("SNIMEK ", out)
		get_tree().quit()

func _zavri(n: Node) -> void:
	if n is MeshInstance3D and n.mesh and n.find_blend_shape_by_name("mrknuti") >= 0:
		n.set_blend_shape_value(n.find_blend_shape_by_name("mrknuti"), 1.0)
	for c in n.get_children():
		if c.name == "Oci": c.set_process(false)
		_zavri(c)
