extends SceneTree
## Vodorovne plochy modelu ve vysce sedu a stolu (14. 11.: stan kupce je jedna sit - kde jsou stolicky a stoly).
## TVRZ_SCENA=res://... ; vypise shluky (mrizka 0,4 m) ploch s normalou nahoru ve vysce 0,38-0,55 (sed) a 0,65-0,85 (stul).


func _initialize() -> void:
	var r := (load(OS.get_environment("TVRZ_SCENA")) as PackedScene).instantiate()
	root.add_child(r)
	var shl := {"sed": {}, "stul": {}}
	for n: Node in r.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var f := mi.mesh.get_faces()
		for i in range(0, f.size(), 3):
			var a := mi.global_transform * f[i]
			var b := mi.global_transform * f[i + 1]
			var c := mi.global_transform * f[i + 2]
			var nn := (b - a).cross(c - a)
			if nn.length() < 1e-6 or absf(nn.normalized().y) < 0.95:
				continue
			var s := (a + b + c) / 3.0
			var druh := "sed" if s.y > 0.38 and s.y < 0.55 else ("stul" if s.y > 0.65 and s.y < 0.85 else "")
			if druh == "":
				continue
			var k := Vector2i(roundi(s.x / 0.4), roundi(s.z / 0.4))
			shl[druh][k] = float(shl[druh].get(k, 0.0)) + nn.length() * 0.5
	for druh: String in shl:
		for k: Vector2i in shl[druh]:
			if float(shl[druh][k]) > 0.02:
				print("PLOCHA %s %.1f %.1f %.3f" % [druh, k.x * 0.4, k.y * 0.4, float(shl[druh][k])])
	quit()
