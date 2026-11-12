extends Node
## Hlídač (Míša 12. 11.: „žádné dveře ani vrata nefungují, nabídka je, ale nejde kliknout“): klepnutí na tlačítko dveří musí dveře přepnout – dřív dotyk pohltila plocha ikon přes celou obrazovku.
## test: hráč u dveří, klepnutí (dotyk) na tlačítko Otevřít/Zavřít musí přepnout dveře
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var pr: Node = null
	for k in 400:
		await get_tree().create_timer(0.5, true).timeout
		for c in get_tree().current_scene.get_children():
			if c.get("hv") != null and c.hv != null and c.get("dvere") != null: pr = c
		if pr: break
	if pr.has_method("zavri_nabidku"): pr.zavri_nabidku()
	get_tree().paused = false
	var dv: Node = pr.dvere; var hrac: Node3D = get_tree().current_scene.hrac
	var g: String = ""
	for k in dv.mista:
		if String(dv.druh.get(k, "")) == "dvere": g = k; break
	hrac.global_position = dv.mista[g] - Vector3(0, 1.0, 0) + Vector3(0.3, 0, 0.3)
	for i in 30: await get_tree().physics_frame
	await get_tree().create_timer(0.5, true).timeout
	var b: Button = dv.tlacitko
	print("KLIK_TEST tlacitko viditelne=", b.visible, " text=", b.text, " blizko=", dv._blizko)
	var st0: bool = dv.stav[g]
	var c := get_viewport().get_final_transform() * b.get_global_rect().get_center()
	var mm := InputEventMouseMotion.new(); mm.position = c; mm.global_position = c; Input.parse_input_event(mm)
	await get_tree().process_frame; await get_tree().process_frame
	var hc := get_viewport().gui_get_hovered_control()
	print("KLIK_TEST pod prstem: ", hc, " ", hc.get_path() if hc else "", " tlacitko ", b.get_path(), " rect ", b.get_global_rect())
	for pressed in [true, false]:
		var t := InputEventMouseButton.new(); t.position = c; t.global_position = c; t.pressed = pressed; t.button_index = MOUSE_BUTTON_LEFT
		Input.parse_input_event(t)
		await get_tree().process_frame
	await get_tree().create_timer(0.5, true).timeout
	print("KLIK_TEST dvere ", g, " pred=", st0, " po=", dv.stav[g], " -> ", "OK" if dv.stav[g] != st0 else "CHYBA")
	get_tree().quit()
