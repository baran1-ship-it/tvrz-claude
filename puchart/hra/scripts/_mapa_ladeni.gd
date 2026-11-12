extends Node
const S := "/tmp/claude-0/-home-user-tvrz-claude/e20a223d-9259-5216-9959-9bf0b880cfe4/scratchpad/"
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var pr: Node = null
	for k in 400:
		await get_tree().create_timer(0.5, true).timeout
		for c in get_tree().current_scene.get_children():
			if c.get("hv") != null and c.hv != null and c.get("mapa") != null: pr = c
		if pr: break
	await get_tree().create_timer(9.0, true).timeout
	get_viewport().get_texture().get_image().save_png(S + "menu.png")
	pr.menu.show_page("play"); await get_tree().create_timer(1.0, true).timeout
	get_viewport().get_texture().get_image().save_png(S + "menu_play.png")
	pr._akce("sandbox", null)
	await get_tree().create_timer(1.0, true).timeout
	print("LAD day ", pr.hv.day, " dark ", pr.hv.predmety.is_dark(), " poloha ", pr.hrac.global_position)
	pr.otevri_nabidku(); pr.menu.show_page("settings"); await get_tree().create_timer(1.0, true).timeout
	get_viewport().get_texture().get_image().save_png(S + "nastaveni.png")
	pr.zavri_nabidku()
	pr.mapa.show_map(); await get_tree().create_timer(1.0, true).timeout
	get_viewport().get_texture().get_image().save_png(S + "mapa.png")
	pr.mapa._cur = pr.mapa._to_screen(pr.mapa._map_rect(), pr.mapa.mista[0]["p"]) - Vector2(0, 34); pr.mapa._update_hover(); pr.mapa._c.queue_redraw(); await get_tree().create_timer(0.5, true).timeout
	get_viewport().get_texture().get_image().save_png(S + "mapa_hover.png")
	pr.mapa.sel = 2; pr.mapa._ask(); pr.mapa._c.queue_redraw(); await get_tree().create_timer(0.5, true).timeout
	get_viewport().get_texture().get_image().save_png(S + "mapa_dotaz.png")
	pr.mapa.asking = false; pr.mapa.close()
	for m in pr.mapa.mista:
		var h0: float = pr.hlavni.den.hour
		await pr.mapa.cestuj(m["cil"], m["pohled"], 0.5)
		for i in 60: await get_tree().physics_frame
		var t: float = pr.hlavni.svet.vyska(pr.hrac.global_position.x, pr.hrac.global_position.z)
		print("LAD cesta %s -> %s teren %.2f na_zemi %s cas %.2f->%.2f" % [m["nazev"], pr.hrac.global_position, t, pr.hrac.is_on_floor(), h0, pr.hlavni.den.hour])
	pr.hlavni.den.set_time("noc", 0.01); await get_tree().create_timer(1.0, true).timeout
	print("LAD noc dark ", pr.hv.predmety.is_dark(), " ", pr.hlavni.den.current)
	get_tree().quit()
