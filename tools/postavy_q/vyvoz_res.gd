extends SceneTree
# vyvoz importovane sceny (bez zdroje v kontejneru) do glb: RES=res://... CIL=/cesta.glb
func _initialize() -> void:
	var ps := load(OS.get_environment("RES")) as PackedScene
	if ps == null:
		print("VYVOZ nenacteno"); quit(); return
	var n := ps.instantiate()
	get_root().add_child(n)
	var doc := GLTFDocument.new()
	var st := GLTFState.new()
	var e := doc.append_from_scene(n, st)
	e = doc.write_to_filesystem(st, OS.get_environment("CIL")) if e == OK else e
	print("VYVOZ ", e)
	quit()
