extends CanvasLayer
## Po měření (nebo hned, když měření není) předá ovládání hráči: tlačítka běh a rychlé přesuny na zajímavá místa.
## Místa = pravidla (hra/data/mista.json).
var hlavni: Node
var hrac: CharacterBody3D
var mista: Array
var _nahoru: Button
var _dolu: Button
var nabidka: Control        # svitek s tlačítky vlevo (pad.gd: Start = výběr křížem)
var mapa: CanvasLayer
var dvere: Node
var pad_nabidka := false
var _pismo: Font
var _n_tl := 0

## Tlačítko jako pruh pergamenu (Havran styl.gd): inkoust, vybrané červeně s pečetí; 4 varianty pruhu.
func _svitek(b: Button, fs := 24) -> void:
	if _pismo == null: _pismo = load("res://fonty/GrenzeGotisch-Medium.ttf")
	Styl.tlacitko_pruh(b, _pismo, fs, _n_tl); _n_tl += 1

func otevri_nabidku() -> void:
	nabidka.visible = true; pad_nabidka = true
	var prvni := nabidka.find_children("*", "Button", true, false)
	if prvni.size() > 0: (prvni[0] as Button).grab_focus()

func zavri_nabidku() -> void:
	pad_nabidka = false
	var f := get_viewport().gui_get_focus_owner()
	if f: f.release_focus()

func pouzij() -> void:   # A: vrata a dveře na dosah
	if dvere and dvere._blizko != "": dvere.prepni(dvere._blizko)

func zacni(h: Node, p: CharacterBody3D) -> void:
	hlavni = h; hrac = p
	mista = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista.json"))["mista"]
	var box := VBoxContainer.new(); box.position = Vector2(20, 180); nabidka = box
	box.add_theme_constant_override("separation", 4)
	add_child(box)
	var dv: Node = load("res://scripts/dvere.gd").new(); dv.name = "Dvere"; add_child(dv); dv.zacni(h, self); dvere = dv   # vrata a dveře
	var pd: Node = load("res://scripts/pad.gd").new(); pd.name = "Pad"; pd.proch = self; pd.hrac = p; add_child(pd)
	var b := Button.new(); b.text = "Běh: ne"; b.custom_minimum_size = Vector2(230, 64)
	_svitek(b)
	b.pressed.connect(func(): hrac.bezi = not hrac.bezi; b.text = "Běh: " + ("ano" if hrac.bezi else "ne"))
	box.add_child(b)
	var volby := [1.0, 0.75, 0.6]
	if FileAccess.file_exists("res://data/rozpocty.json"):
		volby = JSON.parse_string(FileAccess.get_file_as_string("res://data/rozpocty.json"))["obraz_3d"]["volby"]
	var bo := Button.new(); bo.custom_minimum_size = Vector2(230, 64); _svitek(bo)
	bo.text = "Obraz 3D: %d %%" % roundi(get_viewport().scaling_3d_scale * 100)
	bo.pressed.connect(func():   # rozlišení 3D dokola podle rozpocty.json (porovnat ostrost a plynulost)
		var i := 0
		for k in volby.size():
			if absf(float(volby[k]) - get_viewport().scaling_3d_scale) < 0.01: i = k
		get_viewport().scaling_3d_scale = float(volby[(i + 1) % volby.size()])
		bo.text = "Obraz 3D: %d %%" % roundi(get_viewport().scaling_3d_scale * 100))
	box.add_child(bo)
	var bl := Button.new(); bl.text = "Létání: ne"; bl.custom_minimum_size = Vector2(230, 64)
	_svitek(bl)
	bl.pressed.connect(func(): hrac.prepni_let(); bl.text = "Létání: " + ("ano" if hrac.leti else "ne"); _nahoru.visible = hrac.leti; _dolu.visible = hrac.leti)
	box.add_child(bl)
	# nahoru/dolů při létání: držená tlačítka vpravo dole (pravá půlka obrazovky je rozhled, tlačítka mají přednost)
	var vp := get_viewport().get_visible_rect().size
	for i in 2:
		var t := Button.new(); t.text = "▲ nahoru" if i == 0 else "▼ dolů"; t.custom_minimum_size = Vector2(200, 110)
		_svitek(t, 28); t.position = Vector2(vp.x - 230, vp.y - 260 + i * 130); t.visible = false
		var smer := 1.0 if i == 0 else -1.0
		t.button_down.connect(func(): hrac.vzhuru = smer)
		t.button_up.connect(func(): hrac.vzhuru = 0.0)
		add_child(t)
		if i == 0: _nahoru = t
		else: _dolu = t
		hrac.ui.append(t)
	mapa = load("res://scripts/mapa.gd").new(); mapa.hrac = hrac; add_child(mapa)
	var bm := Button.new(); bm.text = "Mapa"; bm.custom_minimum_size = Vector2(230, 64)
	_svitek(bm); bm.pressed.connect(mapa.prepni)
	box.add_child(bm)
	# místa: posuvný seznam pod pevnými tlačítky (16 míst se na tablet nevejde – snímek Míši 30. 10.)
	var sc := ScrollContainer.new(); sc.custom_minimum_size = Vector2(250, maxf(200.0, get_viewport().get_visible_rect().size.y - 180.0 - 4 * 70.0 - 20.0))
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	box.add_child(sc)
	var sez := VBoxContainer.new(); sc.add_child(sez)
	for m in mista:
		var t := Button.new(); t.text = m["nazev"]; t.custom_minimum_size = Vector2(230, 56)
		_svitek(t, 22)
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
