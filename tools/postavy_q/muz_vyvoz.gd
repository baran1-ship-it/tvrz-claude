extends SceneTree
# Kopie zkusebniho skriptu: FBX dat do res://zk_muz/muz01.fbx (mimo build/ - .gdignore), --import, pak
# 25. 11.: Blender nacte UE4 FBX kostru jen jako prazdne objekty - Godot (ufbx) ji nacte; vyvoz do glb pro Blender
func _initialize() -> void:
	var jm := OS.get_environment("MUZ") if OS.get_environment("MUZ") != "" else "muz01"
	var ps := load("res://zk_muz/%s.fbx" % jm) as PackedScene
	if ps == null:
		print("MUZ nenacteno"); quit(); return
	var n := ps.instantiate()
	get_root().add_child(n)
	# hlava s tvarovymi klici (vyrazy tvare) se vyvezla bez trojuhelniku (blend_shape_count chyba) - klice pryc
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m := (mi as MeshInstance3D).mesh as ArrayMesh
		if m == null or m.get_blend_shape_count() == 0:
			continue
		var nova := ArrayMesh.new()
		for i in m.get_surface_count():
			nova.add_surface_from_arrays(m.surface_get_primitive_type(i), m.surface_get_arrays(i))
			nova.surface_set_material(i, m.surface_get_material(i))
		(mi as MeshInstance3D).mesh = nova
		print("VYVOZ bez tvarovych klicu ", mi.name)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e := doc.append_from_scene(n, st)
	e = doc.write_to_filesystem(st, "/tmp/claude-0/muzi/%s.glb" % jm) if e == OK else e
	print("VYVOZ ", e)
	quit()
