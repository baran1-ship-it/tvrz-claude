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
	if OS.get_environment("PUCHART_LADENI") == "jesle":
		for p: Dictionary in fu.polozky_:
			if p["druh"] != "jesle": continue
			fu.nasyp(p)
			var d: Node3D = p["dum"]
			pohledy = [["predni", d.global_transform * Vector3(-0.6, 1.75, -2.75), d.global_transform * Vector3(-0.6, 1.9, -4.1)],
				["shora", d.global_transform * Vector3(-0.2, 2.5, -3.0), d.global_transform * Vector3(-0.7, 1.95, -4.05)],
				["detail", d.global_transform * Vector3(-0.3, 2.25, -3.3), d.global_transform * Vector3(-0.6, 2.0, -4.0)]]
			break
	for uz: Node3D in ([] if not pohledy.is_empty() else h.find_children("Kovadlina_1393", "Node3D", true, false)):
		var t := uz.global_transform
		pohledy = [["jako_kcd2", t * Vector3(0.05, 1.12, 1.75), t * Vector3(0.05, 0.58, 0.0)],
			["kovarna", t * Vector3(1.6, 1.7, 2.6), t * Vector3(-0.2, 0.7, -0.6)],
			["detail", t * Vector3(0.45, 1.15, 0.7), t * Vector3(0.05, 0.72, 0.0)]]
		break
	if pohledy.is_empty(): print("LADENI nic nenalezeno"); get_tree().quit(); return
	for c in get_tree().root.find_children("*", "CanvasLayer", true, false): (c as CanvasLayer).visible = false
	for p: Array in pohledy:
		cam.look_at_from_position(p[1], p[2], Vector3.UP)
		for sv in (2 if OS.get_environment("PUCHART_LADENI") == "jesle" else 1):
			var lampa: OmniLight3D = null
			if sv == 1: lampa = OmniLight3D.new(); lampa.omni_range = 7.0; lampa.light_energy = 1.4; lampa.light_color = Color(1.0, 0.93, 0.82); cam.add_child(lampa)
			for i in 45: await get_tree().process_frame
			var f := "%s%s_%s.png" % [out, p[0], ["hra", "lampa"][sv]]
			get_viewport().get_texture().get_image().save_png(f); print("LADENI snimek ", f)
			if lampa: lampa.queue_free()
	get_tree().quit()
