extends SceneTree
## Rozbor automatickych LOD importu (Misa 0.99994 r. 67 „hnede klobouky v trave“, r. 49 „deska“): pro modely rostlin
## a predmetu vypise pocet trojuhelniku LOD0 a kazde urovne LOD (edge_length) - kolik z tvaru zbyde na tabletu
## (mesh_lod_threshold 10). Spusteni: tools/beh.sh lod cmd godot --headless --path . -s res://tools/lod_rozbor.gd
## Volitelne LOD_MODELY="res://...glb;..." (vychozi: vsechny modely/rostliny/*.glb).

func _initialize() -> void:
	var cesty: Array = []
	if OS.has_environment("LOD_MODELY"):
		cesty = Array(OS.get_environment("LOD_MODELY").split(";", false))
	else:
		for f in DirAccess.get_files_at("res://modely/rostliny"):
			if f.ends_with(".glb"):
				cesty.append("res://modely/rostliny/" + f)
	for c: String in cesty:
		var ps := load(c) as PackedScene
		if ps == null:
			continue
		var n := ps.instantiate()
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var m: Mesh = (mi as MeshInstance3D).mesh
			if m == null:
				continue
			var su = m.get("_surfaces")
			var txt := []
			if su is Array:
				for s: Dictionary in su:
					var t0 := int(s.get("index_count", 0)) / 3
					var lods: Array = []
					var ld = s.get("lods", [])
					for i in range(0, (ld as Array).size(), 2):
						lods.append("%.3f:%d" % [float(ld[i]), (ld[i + 1] as PackedByteArray).size() / (6 if int(s.get("vertex_count", 0)) <= 65535 else 12)])
					txt.append("%d troj, LOD %s" % [t0, str(lods)])
			print("LOD %s %s aabb %s %s" % [c.get_file(), mi.name, m.get_aabb().size, str(txt)])
		n.free()
	quit()
