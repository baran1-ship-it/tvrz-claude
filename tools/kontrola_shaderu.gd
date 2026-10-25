extends SceneTree
## Rychla kontrola shaderu (beh.sh pred focenim): kazdy shaders/*.gdshader na kouli, jeden snimek v opengl3
## (gl_compatibility jako tablet) - SHADER ERROR za par sekund, ne az po stavbe sveta.
##   xvfb-run godot --path . --rendering-driver opengl3 --rendering-method gl_compatibility -s res://tools/kontrola_shaderu.gd

func _init() -> void:
	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(0, 0, 3)
	var jen := OS.get_environment("SHADERY").split(" ", false)
	for f: String in DirAccess.get_files_at("res://shaders"):
		if not f.ends_with(".gdshader") or (not jen.is_empty() and not jen.has("shaders/" + f)):
			continue
		var sh := load("res://shaders/" + f) as Shader
		if sh == null or sh.get_mode() != Shader.MODE_SPATIAL:
			continue
		var mi := MeshInstance3D.new()
		mi.mesh = SphereMesh.new()
		var m := ShaderMaterial.new()
		m.shader = sh
		mi.material_override = m
		root.add_child(mi)
	await process_frame
	await process_frame
	await process_frame
	print("kontrola shaderu hotova")
	quit()
