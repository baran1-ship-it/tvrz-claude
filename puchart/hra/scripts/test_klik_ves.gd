extends Node
## Hlídač dveří ve vsi (Míša 13. 11.: „jako na hradě tak i ves, hospoda, hájovna – funkční dveře, vrata, vrátka“):
## hráč u dveří domu ve vsi (skupina dveře@dům z data/pohyb_mista.json), klepnutí (dotyk) na tlačítko Otevřít/Zavřít musí
## dveře přepnout; počet dveří domů a vrat/vrátek plotů (ves.gd pohyb_dily) musí být nenulový. Vzor test_klik.gd.
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
	var n_dum := 0; var n_plot := 0
	for k: String in dv.dily:
		if k.contains("@"): n_dum += 1
		elif k.begins_with("ves_"): n_plot += 1
	print("KLIK_VES_TEST dveří domů %d, vrat a vrátek plotů %d" % [n_dum, n_plot])
	for k: String in dv.mista:
		if String(dv.druh.get(k, "")) == "dvere" and k.contains("@") and k.contains("Vstup"): g = k; break
	if g == "":
		print("KLIK_VES_TEST dvere ? -> CHYBA (žádné dveře domu)"); get_tree().quit(); return
	hrac.global_position = dv.mista[g] - Vector3(0, 1.0, 0) + Vector3(0.3, 0, 0.3)
	for i in 30: await get_tree().physics_frame
	await get_tree().create_timer(0.5, true).timeout
	var b: Button = dv.tlacitko
	print("KLIK_VES_TEST tlacitko viditelne=", b.visible, " text=", b.text, " blizko=", dv._blizko)
	if String(dv._blizko).contains("@"): g = dv._blizko   # nejbližší dveře domu (u vstupu mohou být blíž dveře do jizby)
	var st0: bool = dv.stav[g]
	var c := get_viewport().get_final_transform() * b.get_global_rect().get_center()
	var mm := InputEventMouseMotion.new(); mm.position = c; mm.global_position = c; Input.parse_input_event(mm)
	await get_tree().process_frame; await get_tree().process_frame
	var hc := get_viewport().gui_get_hovered_control()
	print("KLIK_VES_TEST pod prstem: ", hc, " ", hc.get_path() if hc else "", " tlacitko ", b.get_path(), " rect ", b.get_global_rect())
	for pressed in [true, false]:
		var t := InputEventMouseButton.new(); t.position = c; t.global_position = c; t.pressed = pressed; t.button_index = MOUSE_BUTTON_LEFT
		Input.parse_input_event(t)
		await get_tree().process_frame
	await get_tree().create_timer(0.5, true).timeout
	print("KLIK_VES_TEST dvere ", g, " pred=", st0, " po=", dv.stav[g], " -> ", "OK" if dv.stav[g] != st0 and n_dum > 0 and n_plot > 0 else "CHYBA")
	get_tree().quit()
