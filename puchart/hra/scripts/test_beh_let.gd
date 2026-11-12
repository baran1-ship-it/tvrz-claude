extends Node
## test: dotyk na kruh Běh přepne hrac.bezi, na kruh Let hrac.leti (Havran hud.gd; Míša 12. 11.), a znovu zpět
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var pr: Node = null
	for k in 400:
		await get_tree().create_timer(0.5, true).timeout
		for c in get_tree().current_scene.get_children():
			if c.get("hv") != null and c.hv != null and c.get("kruhy") != null: pr = c
		if pr: break
	pr._akce("sandbox", null); await get_tree().create_timer(1.0, true).timeout
	var h: Node = pr.hrac; var ok := true
	for kolo in 2:
		for co in ["beh", "let"]:
			var pred: bool = h.bezi if co == "beh" else h.leti
			var c: Vector2 = pr.kruhy.run_c() if co == "beh" else pr.kruhy.let_c()
			var mm := InputEventMouseMotion.new(); mm.position = c; mm.global_position = c; Input.parse_input_event(mm)
			await get_tree().process_frame; await get_tree().process_frame
			var hc := get_viewport().gui_get_hovered_control()
			print("BEHLET_TEST pod prstem ", hc.get_path() if hc else "nic", " bod ", c, " rect ", pr.kruhy.get_global_rect(), " vid ", pr.kruhy.is_visible_in_tree(), " has ", pr.kruhy._has_point(c), " mys ", Input.mouse_mode, " filtr ", pr.kruhy.mouse_filter)
			for st in [true, false]:
				var t := InputEventScreenTouch.new(); t.position = c; t.pressed = st; t.index = 0
				Input.parse_input_event(t); await get_tree().process_frame
			await get_tree().create_timer(0.3, true).timeout
			var po: bool = h.bezi if co == "beh" else h.leti
			print("BEHLET_TEST %s %s -> %s nahoru_viditelne %s" % [co, pred, po, pr._nahoru.visible])
			ok = ok and po != pred and (co != "let" or pr._nahoru.visible == po)
	print("BEHLET_TEST ", "OK" if ok else "CHYBA")
	get_tree().quit()
