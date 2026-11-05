extends SceneTree
## Snimek sad postav bez sveta (vzhled obyvatel, scripts/vzhled.gd): rada postav s klipem v case, slunce se stiny.
## Jen pres tools/beh.sh (na pozadi):
##   TVRZ_FOTO_VZHLED="soubor.png;sada1,sada2,...;klip;cas_s;zaber|..." tools/beh.sh fv cmd xvfb-run -a \
##     -s "-screen 0 1280x720x24" godot --path . --rendering-driver opengl3 --rendering-method gl_compatibility \
##     --resolution 1280x720 -s res://tools/foto_vzhled.gd
## zaber: celek (cela postava), tvar (hlavy zblizka), bok (z boku, chuze - sukne a nohy), sed (z boku dole)
## Vypise DIAG radky: sada, trojuhelniky LOD0 a LOD1 (prvni uroven LOD z importu), povrchy.

const AnimUal := preload("res://scripts/anim_ual.gd")
const Vzhled := preload("res://scripts/vzhled.gd")


func _initialize() -> void:
	_beh.call_deferred()


static func troj(mesh: Mesh) -> Array:
	## [LOD0, LOD1] trojuhelniky (soucet povrchu); LOD1 = prvni uroven automatickych LOD importu (0 = zadne)
	var t0 := 0
	var t1 := 0
	for s in mesh.get_surface_count():
		var d: Dictionary = RenderingServer.mesh_get_surface(mesh.get_rid(), s)
		var ic: int = int(d.get("index_count", 0))
		t0 += ic / 3 if ic > 0 else int(d.get("vertex_count", 0)) / 3
		var lods: Array = d.get("lods", [])
		if not lods.is_empty():
			t1 += (lods[0]["index_data"] as PackedByteArray).size() / (2 if int(d.get("vertex_count", 0)) <= 65535 else 4) / 3
		else:
			t1 += ic / 3
	return [t0, t1]


func _beh() -> void:
	var spec := OS.get_environment("TVRZ_FOTO_VZHLED")
	var koren := Node3D.new()
	root.add_child(koren)
	var env := Environment.new()
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sky.sky_material = sm
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.8
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	var we := WorldEnvironment.new()
	we.environment = env
	koren.add_child(we)
	var sl := DirectionalLight3D.new()
	sl.rotation_degrees = Vector3(-42, 30, 0)
	sl.light_energy = 1.1
	sl.shadow_enabled = true
	sl.directional_shadow_max_distance = 20.0
	koren.add_child(sl)
	var zem := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(30, 30)
	zem.mesh = pm
	var zm := StandardMaterial3D.new()
	zm.albedo_color = Color(0.32, 0.36, 0.22)
	zem.material_override = zm
	koren.add_child(zem)
	var cam := Camera3D.new()
	koren.add_child(cam)
	cam.current = true
	cam.fov = 40.0
	for zaznam: String in spec.split("|", false):
		var p := zaznam.split(";")
		var soubor := p[0]
		var sady := p[1].split(",", false)
		var klipy := (p[2] if p.size() > 2 else "Idle_Loop").split(",", false)
		var cas := float(p[3]) if p.size() > 3 else 0.5
		var zaber := p[4] if p.size() > 4 else "celek"
		var skupina := Node3D.new()
		koren.add_child(skupina)
		var n := sady.size()
		var roz := 0.95 if zaber != "tvar" else 0.62
		for i in n:
			var o := {"id": sady[i], "vzhled": sady[i], "muz": true}
			var mt := Vzhled.model(skupina, o, 200.0)
			if mt.is_empty():
				print("DIAG chybi sada ", sady[i])
				continue
			var uzel: Node3D = mt[0]
			var kostra: Skeleton3D = mt[1]
			uzel.position = Vector3((i - (n - 1) * 0.5) * roz, 0, 0)
			if zaber == "bok":
				uzel.rotation_degrees.y = 90.0
			var ap := AnimationPlayer.new()
			uzel.add_child(ap)
			ap.root_node = NodePath("..")
			ap.add_animation_library("", AnimUal.knihovna(String(uzel.get_path_to(kostra))))
			var klip := klipy[i % klipy.size()]
			if ap.has_animation(klip):
				ap.play(klip)
				ap.seek(cas + i * 0.13, true)
				ap.pause()
			else:
				print("DIAG chybi klip ", klip)
			for g: GeometryInstance3D in mt[2]:
				var mi := g as MeshInstance3D
				var t := troj(mi.mesh)
				print("DIAG sada %s troj LOD0 %d LOD1 %d povrchu %d" % [sady[i], t[0], t[1], mi.mesh.get_surface_count()])
		var sirka := n * roz
		match zaber:
			"tvar":
				cam.fov = 30.0
				cam.position = Vector3(0, 1.62, maxf(1.2, sirka * 1.25))
				cam.look_at(Vector3(0, 1.56, 0))
			"bok", "sed":
				cam.fov = 40.0
				cam.position = Vector3(0, 0.9, maxf(3.0, sirka * 1.5))
				cam.look_at(Vector3(0, 0.8, 0))
			_:
				cam.fov = 40.0
				cam.position = Vector3(0, 1.1, maxf(3.2, sirka * 1.45))
				cam.look_at(Vector3(0, 0.95, 0))
		for _k in 6:
			await process_frame
		await RenderingServer.frame_post_draw
		var img := root.get_viewport().get_texture().get_image()
		DirAccess.make_dir_recursive_absolute(soubor.get_base_dir())
		img.save_png(soubor)
		print("DIAG snimek ", soubor)
		skupina.queue_free()
		await process_frame
	quit(0)
