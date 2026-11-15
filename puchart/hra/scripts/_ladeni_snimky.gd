extends Node
## DOČASNÝ ladicí skript (smazat): snímky kovadliny v kovárně ve světle hry.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var h := get_parent()
	h.set("_foto", "")
	for i in 30: await get_tree().process_frame
	var cl := CanvasLayer.new(); add_child(cl)
	var fu: Node = load("res://scripts/funkce.gd").new(); cl.add_child(fu); fu.zacni(h, cl)
	var cam := h.hrac.get_node("Kamera") as Camera3D
	var out := OS.get_environment("PUCHART_LADENI_OUT")
	var pohledy: Array = []
	for uz: Node3D in h.find_children("Kovadlina_1393", "Node3D", true, false):
		var t := uz.global_transform
		pohledy = [["jako_kcd2", t * Vector3(0.05, 1.12, 1.75), t * Vector3(0.05, 0.58, 0.0)],
			["kovarna", t * Vector3(1.6, 1.7, 2.6), t * Vector3(-0.2, 0.7, -0.6)],
			["detail", t * Vector3(0.45, 1.15, 0.7), t * Vector3(0.05, 0.72, 0.0)]]
		break
	if pohledy.is_empty(): print("LADENI nic nenalezeno"); get_tree().quit(); return
	for c in get_tree().root.find_children("*", "CanvasLayer", true, false): (c as CanvasLayer).visible = false
	for p: Array in pohledy:
		cam.look_at_from_position(p[1], p[2], Vector3.UP)
		for i in 45: await get_tree().process_frame
		var f := "%s%s_hra.png" % [out, p[0]]
		get_viewport().get_texture().get_image().save_png(f); print("LADENI snimek ", f)
	get_tree().quit()
