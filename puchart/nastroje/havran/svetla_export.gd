extends SceneTree
func _init():
	for f in ["p_drzak_louce-2fc404f9c2", "p_louc-b31df8ffbc", "p_svicen-30ee3ad65c", "p_svicen_stojaci-2f727ef976"]:
		print("pack ", f, " ", ProjectSettings.load_resource_pack("/tmp/claude-0/hv_pck/%s.pck" % f, false))
	for n in ["drzak_louce", "louc", "svicen", "svicen_stojaci"]:
		var p := "res://modely/predmety/%s.glb" % n
		if not ResourceLoader.exists(p): print("NEMA ", n); continue
		var sc: PackedScene = load(p); var node := sc.instantiate()
		var gl := GLTFDocument.new(); var st := GLTFState.new()
		var e := gl.append_from_scene(node, st)
		print(n, " export ", e, " ", gl.write_to_filesystem(st, "/tmp/claude-0/hvx/%s.glb" % n))
	quit()
