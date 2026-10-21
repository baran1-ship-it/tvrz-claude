extends SceneTree
## Rozbor site tvrze (0.59 LOD): sitě podle poctu trojuhelniku, rozmer, plochy. godot --headless -s tools/rozbor_tvrze.gd


func _init() -> void:
	var sc: PackedScene = load("res://modely/tvrz.glb")
	var root := sc.instantiate()
	var radky: Array = []
	var celk := 0
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var m := mi.mesh
		if m == null:
			continue
		var t := 0
		for s in m.get_surface_count():
			var a := m.surface_get_arrays(s)
			var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
			t += idx.size() / 3 if idx.size() > 0 else (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
		celk += t
		radky.append([t, String(root.get_path_to(mi)), m.get_surface_count(), m.get_aabb().size])
	radky.sort_custom(func(x: Array, y: Array) -> bool: return x[0] > y[0])
	print("TVRZ celkem %d troj, %d siti" % [celk, radky.size()])
	for r: Array in radky.slice(0, 40):
		print("  %8d  ploch %2d  %s  %s" % [r[0], r[2], r[3], r[1]])
	quit()
