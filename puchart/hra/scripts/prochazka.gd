extends CanvasLayer
## Po měření (nebo hned, když měření není) předá ovládání hráči: tlačítka běh a rychlé přesuny na zajímavá místa.
## Místa = pravidla (hra/data/mista.json).
var hlavni: Node
var hrac: CharacterBody3D
var mista: Array
var _nahoru: Button
var _dolu: Button

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	mista = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista.json"))["mista"]
	var box := VBoxContainer.new(); box.position = Vector2(20, 180)
	add_child(box)
	var b := Button.new(); b.text = "Běh: ne"; b.custom_minimum_size = Vector2(230, 64)
	b.add_theme_font_size_override("font_size", 24)
	b.pressed.connect(func(): hrac.bezi = not hrac.bezi; b.text = "Běh: " + ("ano" if hrac.bezi else "ne"))
	box.add_child(b)
	var bl := Button.new(); bl.text = "Létání: ne"; bl.custom_minimum_size = Vector2(230, 64)
	bl.add_theme_font_size_override("font_size", 24)
	bl.pressed.connect(func(): hrac.prepni_let(); bl.text = "Létání: " + ("ano" if hrac.leti else "ne"); _nahoru.visible = hrac.leti; _dolu.visible = hrac.leti)
	box.add_child(bl)
	# nahoru/dolů při létání: držená tlačítka vpravo dole (pravá půlka obrazovky je rozhled, tlačítka mají přednost)
	var vp := get_viewport().get_visible_rect().size
	for i in 2:
		var t := Button.new(); t.text = "▲ nahoru" if i == 0 else "▼ dolů"; t.custom_minimum_size = Vector2(200, 110)
		t.add_theme_font_size_override("font_size", 28); t.position = Vector2(vp.x - 230, vp.y - 260 + i * 130); t.visible = false
		var smer := 1.0 if i == 0 else -1.0
		t.button_down.connect(func(): hrac.vzhuru = smer)
		t.button_up.connect(func(): hrac.vzhuru = 0.0)
		add_child(t)
		if i == 0: _nahoru = t
		else: _dolu = t
		hrac.ui.append(t)
	var mapa: CanvasLayer = load("res://scripts/mapa.gd").new(); mapa.hrac = hrac; add_child(mapa)
	var bm := Button.new(); bm.text = "Mapa"; bm.custom_minimum_size = Vector2(230, 64)
	bm.add_theme_font_size_override("font_size", 24); bm.pressed.connect(mapa.prepni)
	box.add_child(bm)
	# místa: posuvný seznam pod pevnými tlačítky (16 míst se na tablet nevejde – snímek Míši 30. 10.)
	var sc := ScrollContainer.new(); sc.custom_minimum_size = Vector2(250, maxf(200.0, get_viewport().get_visible_rect().size.y - 180.0 - 3 * 70.0 - 20.0))
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	box.add_child(sc)
	var sez := VBoxContainer.new(); sc.add_child(sez)
	for m in mista:
		var t := Button.new(); t.text = m["nazev"]; t.custom_minimum_size = Vector2(230, 56)
		t.add_theme_font_size_override("font_size", 22)
		t.pressed.connect(_presun.bind(m))
		sez.add_child(t)
	hrac.ui.append(box)
	_presun(mista[0])

func _presun(m: Dictionary) -> void:
	var p: Array = m["kde"]; var c: Array = m["kam"]
	var y: float = float(m["y"]) if m.has("y") else hlavni.svet.vyska(p[0], p[1])
	hlavni.svet.kolize_ihned(Vector3(p[0], y, p[1]))
	hrac.velocity = Vector3.ZERO
	hrac.position = Vector3(p[0], y + 0.3, p[1])
	hrac.nastav_pohled(atan2(-(c[0] - p[0]), -(c[1] - p[1])), -0.05)
