extends SceneTree
# Tmave karty brizy (misa_17_11 r. 3, novy rozbor 23. 11.): izolovane briza s listi.gdshader jako ve hre,
# vlevo se stinovym telesem koruny (svet._stin_koruny, SHADOWS_ONLY), vpravo bez nej. Slunce jako v poledne.
const Svet := preload("res://scripts/svet.gd")
func _init() -> void:
	var root := Node3D.new()
	get_root().add_child(root)
	var S = Svet.new({})
	var kc: Dictionary = Svet.Pravidla.cti("les_podrost", "koruny")
	for strana in [-1, 1]:
		var sc := (load("res://modely/rostliny/briza.glb") as PackedScene).instantiate() as Node3D
		root.add_child(sc)
		sc.position = Vector3(strana * 6.0, 0, 0)
		for nd in sc.find_children("*", "MeshInstance3D", true, false):
			var mi := nd as MeshInstance3D
			var bb := mi.get_aabb()
			var nm := ArrayMesh.new()
			for si in mi.mesh.get_surface_count():
				nm.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, mi.mesh.surface_get_arrays(si))
				var om := mi.mesh.surface_get_material(si)
				var m: Material = om
				if om is BaseMaterial3D and (om as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
					m = S._listi_shader(om, bb, true)
				nm.surface_set_material(si, m)
			mi.mesh = nm
			if strana < 0:
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				var st := MeshInstance3D.new()
				st.mesh = S._stin_koruny(nm, kc)
				st.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
				mi.add_child(st)
	var zem := MeshInstance3D.new()
	var pm := PlaneMesh.new(); pm.size = Vector2(60, 60); zem.mesh = pm
	root.add_child(zem)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-60, 20, 0)
	sun.shadow_enabled = false
	root.add_child(sun)
	var sky := Sky.new(); sky.sky_material = ProceduralSkyMaterial.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY; env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	var we := WorldEnvironment.new(); we.environment = env; root.add_child(we)
	var cam := Camera3D.new(); root.add_child(cam)
	cam.look_at_from_position(Vector3(0, 6, 18), Vector3(0, 7, 0))
	for k in 10:
		await process_frame
	get_root().get_texture().get_image().save_png("res://build/dbg/briza_bezstinu.png")
	quit()
