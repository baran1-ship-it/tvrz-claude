extends SceneTree
## Ikony předmětů katalogu pískoviště (128 × 128, průhledné pozadí jako ikony Havrana v modely/predmety_h/<id>.png):
## scéna předmětu ve vlastním světě, kamera šikmo shora na obal sítí, slunce + okolní světlo.
##   xvfb-run godot --rendering-driver opengl3 --path hra -s res://../nastroje/godot/ikony_predmetu.gd -- <id> [<id> …]
## (nebo zkopírovat do hra/ jako _ikony.gd – volá nastroje/topeni_modely.py --ikony)
const DIR := "res://modely/predmety_h/"

func _initialize() -> void:
	var ids: Array = Array(OS.get_cmdline_user_args())
	for id in ids:
		var cesta: String = DIR + String(id) + (".tscn" if ResourceLoader.exists(DIR + id + ".tscn") else ".glb")
		if not ResourceLoader.exists(cesta): print("IKONA_CHYBI ", id); continue
		var vp := SubViewport.new(); vp.size = Vector2i(128, 128); vp.transparent_bg = true; vp.own_world_3d = true
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(vp)
		var n: Node3D = (load(cesta) as PackedScene).instantiate()
		if n is RigidBody3D: (n as RigidBody3D).freeze = true
		vp.add_child(n)
		var ab := AABB(); var prvni := true
		for g in n.find_children("*", "MeshInstance3D", true, false):
			var mi := g as MeshInstance3D
			if mi.visibility_range_begin > 0.0: mi.visible = false; continue   # LOD1
			mi.visibility_range_end = 0.0
			var b: AABB = mi.global_transform * mi.get_aabb()
			ab = b if prvni else ab.merge(b); prvni = false
		var c := ab.get_center(); var r := ab.size.length() * 0.5
		var cam := Camera3D.new(); vp.add_child(cam); cam.fov = 30.0
		var smer := Vector3(0.75, 0.62, 1.0).normalized()
		cam.look_at_from_position(c + smer * r / tan(deg_to_rad(15.0)) * 1.05, c, Vector3.UP)
		var sl := DirectionalLight3D.new(); vp.add_child(sl); sl.rotation_degrees = Vector3(-50, 30, 0); sl.light_energy = 1.3
		var env := Environment.new(); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.8, 0.78, 0.74); env.ambient_light_energy = 0.7
		env.background_mode = Environment.BG_CLEAR_COLOR
		var we := WorldEnvironment.new(); we.environment = env; vp.add_child(we)
		for i in 6: await process_frame
		var img := vp.get_texture().get_image()
		img.save_png(ProjectSettings.globalize_path(DIR + String(id) + ".png"))
		print("IKONA ", id)
		vp.queue_free()
	quit()
