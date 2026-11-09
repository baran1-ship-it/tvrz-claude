extends CanvasLayer
## Po měření (nebo hned, když měření není) předá ovládání hráči. Úvod a nabídka (menu.gd, Moravian Battlefield) a menu
## hráče (menu_hrace.gd: mapa, místa, deník) podle Havrana (Míša 9. 11.); na obrazovce jen erb (menu hráče), pauza a při
## létání nahoru/dolů. Běh, létání a obraz 3D jsou v Nastavení. Místa = hra/data/mista.json.
var hlavni: Node
var hrac: CharacterBody3D
var mista: Array
var _nahoru: Button
var _dolu: Button
var nabidka: Control        # horní lišta (erb + pauza) – pad.gd
var mapa: CanvasLayer
var dvere: Node
var menu: CanvasLayer       # menu.gd: úvod + pauza
var menu_hrace: CanvasLayer
var pad_nabidka := false
var _pismo: Font
var _obraz_volby := [1.0, 0.75, 0.6]
var _hudba := 1.0

func _svitek(b: Button, fs := 24, i := 0) -> void:
	if _pismo == null: _pismo = load("res://fonty/GrenzeGotisch-Medium.ttf")
	Styl.tlacitko_pruh(b, _pismo, fs, i)

func otevri_nabidku() -> void:   # Start: pauza (Havran)
	if menu_hrace.open: menu_hrace.zavri()
	get_tree().paused = true
	menu.show_menu(true)

func zavri_nabidku() -> void:
	menu.hide_menu()
	get_tree().paused = false

func otevri_menu_hrace() -> void:
	if menu.visible: return
	menu_hrace.otevri()

func pouzij() -> void:   # A: vrata a dveře na dosah
	if dvere and dvere._blizko != "": dvere.prepni(dvere._blizko)

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	process_mode = Node.PROCESS_MODE_ALWAYS
	mista = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista.json"))["mista"]
	if FileAccess.file_exists("res://data/rozpocty.json"):
		_obraz_volby = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json"))["obraz_3d"]["volby"]
	var dv: Node = load("res://scripts/dvere.gd").new(); dv.name = "Dvere"; add_child(dv); dv.zacni(h, self); dvere = dv   # vrata a dveře
	var pd: Node = load("res://scripts/pad.gd").new(); pd.name = "Pad"; pd.proch = self; pd.hrac = p; add_child(pd)
	# horní lišta: vlevo erb (menu hráče), vpravo pauza
	var vp := get_viewport().get_visible_rect().size
	var lis := Control.new(); lis.set_anchors_preset(Control.PRESET_FULL_RECT); lis.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(lis); nabidka = lis
	var be := Button.new(); be.text = "Deník"; be.custom_minimum_size = Vector2(170, 64); be.position = Vector2(20, 150)
	_svitek(be, 26, 0); be.pressed.connect(otevri_menu_hrace); lis.add_child(be)
	var bp := Button.new(); bp.text = "Nabídka"; bp.custom_minimum_size = Vector2(170, 64); bp.position = Vector2(vp.x - 190, 20)
	_svitek(bp, 26, 1); bp.pressed.connect(otevri_nabidku); lis.add_child(bp)
	hrac.ui.append(be); hrac.ui.append(bp)
	# nahoru/dolů při létání: držená tlačítka vpravo dole
	for i in 2:
		var t := Button.new(); t.text = "▲ nahoru" if i == 0 else "▼ dolů"; t.custom_minimum_size = Vector2(200, 110)
		_svitek(t, 28, i); t.position = Vector2(vp.x - 230, vp.y - 260 + i * 130); t.visible = false
		var smer := 1.0 if i == 0 else -1.0
		t.button_down.connect(func(): hrac.vzhuru = smer)
		t.button_up.connect(func(): hrac.vzhuru = 0.0)
		add_child(t)
		if i == 0: _nahoru = t
		else: _dolu = t
		hrac.ui.append(t)
	mapa = load("res://scripts/mapa.gd").new(); mapa.hrac = hrac; add_child(mapa)
	menu_hrace = load("res://scripts/menu_hrace.gd").new(); menu_hrace.proch = self; add_child(menu_hrace)
	menu = load("res://scripts/menu.gd").new(); add_child(menu)
	menu.action.connect(_akce)
	_nastaveni()
	_presun(mista[0])
	get_tree().paused = true
	menu.play_intro()   # úvod: erb Bočka z Kunštátu, název hry, hudba (Havran)
	if OS.get_environment("PUCHART_MENU_FOTO") != "":   # snímek úvodní nabídky (kontrola vzhledu bez tabletu)
		await get_tree().create_timer(9.0).timeout
		get_viewport().get_texture().get_image().save_png(OS.get_environment("PUCHART_MENU_FOTO")); get_tree().quit()

func _nastaveni() -> void:
	menu.refresh_settings({"beh": "Běh: " + ("ano" if hrac.bezi else "ne"), "let": "Létání: " + ("ano" if hrac.leti else "ne"),
		"obraz": "Obraz 3D: %d %%" % roundi(get_viewport().scaling_3d_scale * 100), "vol:hudba": _hudba})

func _akce(co: String, arg: Variant) -> void:
	match co:
		"play", "resume":
			zavri_nabidku()
		"quit":
			get_tree().quit()
		"set:beh":
			hrac.bezi = not hrac.bezi
		"set:let":
			hrac.prepni_let(); _nahoru.visible = hrac.leti; _dolu.visible = hrac.leti
		"set:obraz":   # rozlišení 3D dokola podle rozpocty.json
			var i := 0
			for k in _obraz_volby.size():
				if absf(float(_obraz_volby[k]) - get_viewport().scaling_3d_scale) < 0.01: i = k
			get_viewport().scaling_3d_scale = float(_obraz_volby[(i + 1) % _obraz_volby.size()])
		"vol:hudba":
			_hudba = float(arg); menu.music.volume_db = linear_to_db(maxf(_hudba, 0.001)) - 6.0
	_nastaveni()

func _presun(m: Dictionary) -> void:
	var p: Array = m["kde"]; var c: Array = m["kam"]
	var y: float = float(m["y"]) if m.has("y") else hlavni.svet.vyska(p[0], p[1])
	hlavni.svet.kolize_ihned(Vector3(p[0], y, p[1]))
	hrac.velocity = Vector3.ZERO
	hrac.position = Vector3(p[0], y + 0.3, p[1])
	hrac.nastav_pohled(atan2(-(c[0] - p[0]), -(c[1] - p[1])), -0.05)
