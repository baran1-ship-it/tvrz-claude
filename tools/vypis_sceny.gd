extends SceneTree
## Vypis uzlu sceny (jmeno, poloha, natoceni, AABB site) - TVRZ_SCENA=res://... (14. 11.: sedaky ve stanu kupce)
## tools/beh.sh vs cmd godot --headless --path . -s res://tools/vypis_sceny.gd


func _initialize() -> void:
	var ps: PackedScene = load(OS.get_environment("TVRZ_SCENA"))
	var r := ps.instantiate()
	root.add_child(r)
	for n: Node in r.find_children("*", "Node3D", true, false):
		var g := n as Node3D
		var bb := ""
		if g is MeshInstance3D and (g as MeshInstance3D).mesh:
			var a := (g as MeshInstance3D).get_aabb()
			bb = " aabb %s..%s" % [str((g.global_transform * a.position).snapped(Vector3.ONE * 0.01)), str((g.global_transform * a.end).snapped(Vector3.ONE * 0.01))]
		print("UZEL %s %s yaw %.0f%s" % [String(r.get_path_to(g)), str(g.global_position.snapped(Vector3.ONE * 0.01)), rad_to_deg(g.global_rotation.y), bb])
	quit()
