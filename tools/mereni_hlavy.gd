extends SceneTree
## Mereni hlavy nastroje (Misa 12. 11.: „na zem dopadne spickou a sekera ostrim, ne na plochu“): pro predmet z drzeni
## s nasadou vrcholy hlavy (horni cast nad nasadou) - rozsah v ose x a z predmetu od osy nasady. Ostri/spicka = strana,
## kam hlava saha dal (u sekery ostri dal nez tylo).
## Spusteni: tools/beh.sh hlava cmd godot --headless --path . -s res://tools/mereni_hlavy.gd

func _initialize() -> void:
	for id: String in ["krumpac", "sekera", "perlik", "kladivo"]:
		var ps: PackedScene = load("res://modely/predmety/%s.glb" % id)
		var n: Node3D = ps.instantiate()
		root.add_child(n)
		var vs: Array = []
		var ymax := -INF
		for mi: Node in n.find_children("*", "MeshInstance3D", true, false):
			var m := (mi as MeshInstance3D).mesh
			var tr := (mi as MeshInstance3D).global_transform
			for si in m.get_surface_count():
				for v: Vector3 in m.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
					var w := tr * v
					vs.append(w)
					ymax = maxf(ymax, w.y)
		var h: Array = vs.filter(func(w: Vector3) -> bool: return w.y > ymax - 0.15)
		var mn := Vector3.INF
		var mx := -Vector3.INF
		for w: Vector3 in h:
			mn = mn.min(w)
			mx = mx.max(w)
		var bx: Vector3 = h[0]
		var bz: Vector3 = h[0]
		for w: Vector3 in h:
			if w.x > bx.x:
				bx = w
			if w.z > bz.z:
				bz = w
		print("HLAVA_BOD %-8s nejdal v +x %s, nejdal v +z %s" % [id, bx.snapped(Vector3.ONE * 0.001), bz.snapped(Vector3.ONE * 0.001)])
		print("HLAVA %-8s vrch y %.3f, hlava x %.3f..%.3f, z %.3f..%.3f (vrcholu %d)" % [id, ymax, mn.x, mx.x, mn.z, mx.z, h.size()])
	quit(0)
