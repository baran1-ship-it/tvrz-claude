extends Node
## Hlídač (chyba louče, Míša 13. 11.: „louče nefungují“): držák s loučí před hráčem, klepnutí prstem na „Zapálit“ v nabídce akcí musí louč zapálit.
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var pr: Node = null
	for k in 400:
		await get_tree().create_timer(0.5, true).timeout
		for c in get_tree().current_scene.get_children():
			if c.get("hv") != null and c.hv != null and c.hv.get("predmety") != null: pr = c
		if pr: break
	if pr.has_method("zavri_nabidku"): pr.zavri_nabidku()
	get_tree().paused = false
	await get_tree().create_timer(2.0, true).timeout
	var P: Node = pr.hv.predmety; var cam := get_viewport().get_camera_3d()
	var p: Vector3 = cam.global_position - cam.global_transform.basis.z * 1.2
	P.spawn({"id": "drzak_louce", "p": p, "yaw": 0.0, "obsah": {}, "louc": true})
	P._refresh_use()
	for i in 20: await get_tree().process_frame
	var ak: Node = pr.get_node("Akce"); var t := []
	for b in ak._tl: if b.visible: t.append(b.text)
	print("LOUC_TEST nabidka ", t, " klice ", ak._klice)
	var i2: int = ak._klice.find("use2")
	if i2 >= 0:
		var b: Button = ak._tl[i2]; var c := get_viewport().get_final_transform() * b.get_global_rect().get_center()
		var mm := InputEventMouseMotion.new(); mm.position = c; mm.global_position = c; Input.parse_input_event(mm)
		await get_tree().process_frame; await get_tree().process_frame
		print("LOUC_TEST pod prstem ", get_viewport().gui_get_hovered_control(), " rect=", b.get_global_rect())
		for pressed in [true, false]:
			var t2 := InputEventMouseButton.new(); t2.position = c; t2.global_position = c; t2.pressed = pressed; t2.button_index = MOUSE_BUTTON_LEFT
			Input.parse_input_event(t2); await get_tree().process_frame
	for i in 10: await get_tree().process_frame
	var rec: Dictionary = P.placed[-1]
	var ok: bool = rec.get("hori", false) and i2 >= 0
	print("LOUC_TEST zapaleni dotykem hori=", rec.get("hori", false), " -> ", "OK" if ok else "CHYBA")
	get_tree().quit()
