extends SceneTree
## Test hlavní nabídky a načítací obrazovky „Blood for Blood“ (Míša 17. 11.) – bez stavby světa:
##   cd hra && xvfb-run -a -s "-screen 0 1600x1000x24" $G --rendering-driver opengl3 --resolution 1600x1000 -s res://scripts/test_nabidka.gd
## Ověří: karty z dat (každá vlastní obrázek, texty jen z hra/data/nacitani.json), karta vidět nejméně cas_min_s i při
## rychlém načtení, prolnutí do černé; nabídka – fokus šipkami/ovladačem (nedostupná položka se přeskočí), A/B, myš
## (najetí vybere, klik potvrdí), dotyk; v nabídce žádná pečeť. Výpis NABIDKA_TEST OK / CHYBA.
## PUCHART_BFB_FOTO=adresář: místo testu snímky obou obrazovek (bfb_menu_*.png, bfb_nacitani_*.png).

var chyby: Array = []
var akce: Array = []


func _initialize() -> void:
	_run.call_deferred()


func ok(c: bool, co: String) -> void:
	print("  ", "OK   " if c else "CHYBA", " ", co)
	if not c: chyby.append(co)


func snimku(n: int) -> void:
	for i in n: await process_frame


func cekej(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _run() -> void:
	var foto := OS.get_environment("PUCHART_BFB_FOTO")
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/nacitani.json"))
	var nac: Node = root.get_node_or_null("Nacitani")
	if nac == null:
		nac = load("res://scripts/nacitani.gd").new(); nac.name = "Nacitani"; root.add_child(nac)
	nac.cfg["predem"] = []   # bez těžkých modelů (test čte jen vlastní data)
	if foto != "":
		await _foto(nac, data, foto)
		quit(); return

	# ---- data karet
	var karty: Array = data.get("karty", [])
	ok(karty.size() >= 12 and karty.size() <= 20, "karet %d (12–20)" % karty.size())
	var obr := {}
	for k: Dictionary in karty:
		obr[k["obrazek"]] = true
		ok(ResourceLoader.exists(String(k["obrazek"])), "obrázek %s" % k["obrazek"])
		ok(String(k.get("ini", "")) != "" and String(k.get("text", "")) != "" and String(k.get("preklad", "")) != "", "texty karty %s" % k.get("id"))
		ok(data.get("popisky_zdroje", {}).has(String(k.get("zdroj", ""))), "popisek zdroje karty %s" % k.get("id"))
	if String(data.get("obrazky_stav", "")) == "ceka_na_commons":   # Commons 17. 11. nedostupné (429) – viz nacitani.json obrazky_stav_popis
		print("  UPOZORNENI každá karta vlastní obrázek: %d obrázků / %d karet – čeká na stažení z Commons (karty_plan %d)" % [obr.size(), karty.size(), data.get("karty_plan", []).size()])
	else:
		ok(obr.size() == karty.size(), "každá karta vlastní obrázek (%d obrázků / %d karet)" % [obr.size(), karty.size()])
	var autori := {}
	for o: Dictionary in data.get("obrazky", []): autori[String(o.get("soubor", ""))] = true
	for o: String in obr: ok(autori.has(o), "autor obrázku v CREDITS (obrazky[]) %s" % o)

	# ---- načítací obrazovka: texty z dat, nejméně cas_min_s, prolnutí do černé
	Engine.time_scale = 4.0   # čas karty se počítá z delta – test běží 4× rychleji
	var v_cerne := [-1.0]
	nac.v_cerne.connect(func() -> void: v_cerne[0] = nac.cas)
	nac.aktivni = true
	# start aplikace (před nabídkou): jen název a linka, žádná karta (Míša 18. 11.)
	nac.zacni()
	await snimku(3)
	ok(nac.uvod and nac._uvod_uzel.visible and not nac._karta_uzel.visible, "start aplikace bez karty s pořekadlem")
	nac.hotovo()
	while nac.bezi and nac.cas < 20.0: await process_frame
	await cekej(1.0)
	v_cerne[0] = -1.0
	# vstup do hry z nabídky: karta
	nac.prechod()
	await snimku(3)
	ok(not nac.uvod and nac._karta_uzel.visible, "vstup do hry z nabídky ukáže kartu")
	var k: Dictionary = nac.karta
	ok(nac.visible and nac.bezi, "karta je na obrazovce")
	ok(nac._citat.text == String(k["text"]) and nac._iniciala.text == String(k["ini"]) and nac._preklad.text == String(k["preklad"]), "pořekadlo z dat")
	ok(nac._misto.text == String(data["texty"]["misto"]) and nac._stav.text == String(data["texty"]["stav"]), "texty obrazovky z dat")
	ok(nac._popisek.text == String(data["popisky_zdroje"][k["zdroj"]]), "popisek zdroje z dat")
	ok(nac._obraz.texture != null, "obrázek karty načten")
	await cekej(0.3)   # prechod() hlásí hotovo hned – karta musí zůstat
	while v_cerne[0] < 0.0 and nac.cas < 20.0: await process_frame
	var mc: float = nac.min_cas()
	ok(v_cerne[0] >= mc + nac.prolnuti() - 0.12, "karta vidět nejméně %.0f s + prolnutí (do černé v %.2f s)" % [mc, v_cerne[0]])   # tolerance ~3 snímky: prolnutí běží tweenem, nac.cas sčítá delta – pod zátěží hlídačů (17. 11.: 10,62 s) se rozejdou o pár snímků
	ok(v_cerne[0] < mc + nac.prolnuti() + 0.6, "po %.0f s jde do hry bez čekání na tlačítko" % mc)
	ok(nac._clona.color.a > 0.99, "prolnutí do černé")
	await cekej(1.0)
	ok(not nac.visible, "po prolnutí obrazovka zmizí")
	Engine.time_scale = 1.0

	# ---- nabídka
	var src := FileAccess.get_file_as_string("res://scripts/menu.gd")
	ok(not src.contains("kresli_pecet") and not src.contains("tlacitko_pruh"), "v hlavní nabídce žádná pečeť")
	var menu: CanvasLayer = load("res://scripts/menu.gd").new()
	root.add_child(menu)
	menu.action.connect(func(w: String, _a: Variant) -> void: akce.append(w))
	menu.saves = [{"file": "user://neni.json", "t": 0, "label": "Příběh – test"}]
	menu.show_menu(false)
	menu.in_game = false
	menu._bg.visible = true
	await snimku(4)
	ok(_txt(menu) == "Nová hra", "fokus na první položce (%s)" % _txt(menu))
	ok(menu._saw_q.get_parsed_text() == String(menu.porekadlo["ini"]) + String(menu.porekadlo["text"]), "pořekadlo v nabídce z dat")
	await _akce("ui_down"); ok(_txt(menu) == "Pokračovat", "šipka dolů → Pokračovat (%s)" % _txt(menu))
	await _joy(JOY_BUTTON_DPAD_DOWN); ok(_txt(menu) == "Nahrát", "ovladač dolů → Nahrát (%s)" % _txt(menu))
	await _akce("ui_down"); ok(_txt(menu) == "Nastavení", "nedostupné Uložit přeskočeno (%s)" % _txt(menu))
	await _akce("ui_up"); ok(_txt(menu) == "Nahrát", "šipka nahoru (%s)" % _txt(menu))
	await _joy(JOY_BUTTON_DPAD_DOWN)
	await _joy(JOY_BUTTON_A)
	ok(menu._busy, "stránka se mění prolnutím")
	await cekej(0.9)
	ok(menu._page == "settings" and menu._panel.modulate.a > 0.99, "A → Nastavení (%s)" % menu._page)
	await _joy(JOY_BUTTON_B)
	await cekej(0.9)
	ok(menu._page == "main", "B → zpět (%s)" % menu._page)
	# myš: najetí vybere, klik potvrdí
	var b := _polozka(menu, "Nastavení")
	await _mys(b, false)
	ok(_txt(menu) == "Nastavení", "najetí myší vybere položku (%s)" % _txt(menu))
	b = _polozka(menu, "Nová hra")
	await _mys(b, true)
	await cekej(0.9)
	ok(menu._page == "play", "klik myší → Nová hra (%s)" % menu._page)
	# dotyk (emulace myši z dotyku jako na tabletu)
	b = _polozka(menu, "Příběh")
	var c := b.get_global_rect().get_center()
	for p in [true, false]:
		var t := InputEventScreenTouch.new(); t.index = 0; t.position = c; t.pressed = p
		Input.parse_input_event(t); Input.flush_buffered_events()
		await snimku(2)
	ok(akce.has("story"), "dotyk → Příběh (akce %s)" % [akce])
	print("NABIDKA_TEST %s%s" % ["OK" if chyby.is_empty() else "CHYBA ", ", ".join(chyby)])
	quit()


func _txt(menu: Node) -> String:
	var b: Button = menu.vybrana()
	return b.text if b else ""


func _polozka(menu: Node, t: String) -> Button:
	for c in menu._box.get_children():
		if c is Button and (c as Button).text == t: return c
	return null


func _akce(a: String) -> void:
	for p in [true, false]:
		var e := InputEventAction.new(); e.action = a; e.pressed = p
		Input.parse_input_event(e); Input.flush_buffered_events()
		await snimku(2)


func _joy(btn: int) -> void:
	for p in [true, false]:
		var e := InputEventJoypadButton.new(); e.button_index = btn; e.pressed = p; e.device = 0
		Input.parse_input_event(e); Input.flush_buffered_events()
		await snimku(2)


func _mys(b: Button, klik: bool) -> void:
	var c := b.get_global_rect().get_center()
	var m := InputEventMouseMotion.new(); m.position = c; m.global_position = c
	Input.parse_input_event(m); Input.flush_buffered_events()
	await snimku(2)
	if not klik: return
	for p in [true, false]:
		var e := InputEventMouseButton.new(); e.button_index = MOUSE_BUTTON_LEFT; e.pressed = p; e.position = c; e.global_position = c
		Input.parse_input_event(e); Input.flush_buffered_events()
		await snimku(2)


func _uloz(cesta: String) -> void:
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(cesta)
	print("FOTO ", cesta)


## Snímky ke schválení: nabídka (výběr na 3. položce jako snímek předlohy, Nastavení) a dvě karty načítání.
func _foto(nac: Node, data: Dictionary, dir: String) -> void:
	var menu: CanvasLayer = load("res://scripts/menu.gd").new()
	root.add_child(menu)
	menu.saves = [{"file": "user://neni.json", "t": 0, "label": "Příběh – 17. 11. 2026  18:40"}]
	menu.settings_text = {"beh": "Běh: ne", "let": "Létání: ne", "obraz": "Obraz 3D: 75 %", "vol:hudba": 1.0}   # jako prochazka.gd _nastaveni
	menu.show_menu(false)
	var karty: Array = data["karty"]
	menu.porekadlo = karty[3]   # stejné pořekadlo jako snímek předlohy (Nehraď sě plotem…)
	Styl.porekadlo(menu._saw_q, String(karty[3]["ini"]), String(karty[3]["text"]), 30, 44, Color(Styl.BFB_INK, 0.92))
	menu._saw_g.text = String(karty[3]["preklad"])
	await snimku(5)
	await _akce("ui_down"); await _akce("ui_down")
	await snimku(5)
	await _uloz(dir + "/bfb_menu_17_11.png")
	await _akce("ui_down"); await _akce("ui_accept")
	await cekej(1.0)
	await _akce("ui_down")
	await cekej(1.0)
	await _uloz(dir + "/bfb_menu_17_11_nastaveni.png")
	menu.queue_free()
	nac.aktivni = true
	for i: int in [0, 1]:
		var idx: int = int(OS.get_environment("PUCHART_BFB_KARTY").split(",")[i]) if OS.get_environment("PUCHART_BFB_KARTY") != "" else i
		nac.zacni()
		nac.nastav_kartu(idx)
		await cekej(1.2)
		nac.prubeh = 0.62; nac._cil = 0.62
		await snimku(3)
		await _uloz(dir + "/bfb_nacitani_17_11%s.png" % ("" if i == 0 else "_%d" % (i + 1)))
		nac.bezi = false
