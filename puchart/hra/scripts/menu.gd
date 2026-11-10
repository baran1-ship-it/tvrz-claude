extends CanvasLayer
## Úvod (erb Bočka z Kunštátu, hudba, název hry) a hlavní nabídka gotickým písmem – převzato z Havrana (scripts/menu.gd,
## Míša 9. 11.: „dej do hry herní menu i úvodní i hráčovo jako v Havranovi, název hry Moravian Battlefield“).
## Stránky: hlavní, nastavení, autoři. Stejné menu slouží i jako pauza ve hře (Start / tlačítko vpravo nahoře).
## Akce posílá signálem action(co, arg) – obsluhuje prochazka.gd.

signal action(what: String, arg: Variant)

const TITLE := "Moravian Battlefield"
const SUBTITLE := "Puchart, léta Páně 1393"
const GOLD := Color(0.93, 0.8, 0.52)
const GOLD_DIM := Color(0.62, 0.53, 0.37)
# autoři a licence: jen na této stránce menu
const CREDITS := [
	"Úvodní obraz: erb pánů z Kunštátu (stříbrný štít, v horní polovině tři černá břevna) podle Siebmacherova erbovníku – Wikimedia Commons „Kunstadt-Wappen1 Sm.png“ (Dorado), volné dílo",
	"Hudba nabídky: „Medieval: Exploration“ – RandomMind (opengameart.org), CC0",
	"Textury, rostliny a předměty: Poly Haven, CC0",
	"Terén: DMR 5G, ČÚZK; vodní síť a cesty: ZABAGED, OpenStreetMap (ODbL)",
	"Hrad podle kreseb a půdorysů GC80T08 a rešerší (docs/reference)",
	"Písmo: Grenze Gotisch (Omnibus-Type), SIL Open Font License",
	"Herní engine: Godot Engine, MIT",
]

var font_title: FontFile
var font_menu: FontFile
var in_game := false            # běží hra: menu je pauza
var settings_text: Dictionary = {}

var _bg: TextureRect
var _shade: ColorRect
var _title: Label
var _sub: Label
var _box: VBoxContainer
var _scroll: ScrollContainer
var _panel: Control
var _intro_t := -1.0
var _page := "main"
var music: AudioStreamPlayer


func _ready() -> void:
	layer = 20
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	font_title = load("res://fonty/GrenzeGotisch-Bold.ttf")
	font_menu = load("res://fonty/GrenzeGotisch-Medium.ttf")
	_bg = TextureRect.new()
	if ResourceLoader.exists("res://obrazky/intro.jpg"): _bg.texture = load("res://obrazky/intro.jpg")
	_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_bg.modulate = Color(1, 1, 1, 0)
	add_child(_bg)
	_shade = ColorRect.new()
	_shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_shade.color = Color(0, 0, 0, 0)
	_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_shade)
	_title = _lab(TITLE, font_title, 96, GOLD)
	_title.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_title.offset_top = 30
	_title.modulate = Color(1, 1, 1, 0)
	add_child(_title)
	_sub = _lab(SUBTITLE, font_menu, 34, Color(0.9, 0.79, 0.55))
	_sub.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_sub.offset_top = 150
	_sub.modulate = Color(1, 1, 1, 0)
	add_child(_sub)
	# CenterContainer přes celou plochu pod nadpisem: tlačítka vždy uprostřed obrazovky
	_panel = CenterContainer.new()
	_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.offset_top = 200
	_panel.offset_bottom = -16
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.visible = false
	add_child(_panel)
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 6)
	_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_scroll = ScrollContainer.new()   # Havran (Míša 0.92): nastavení se nevešlo na tablet – posuvná plocha
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.scroll_deadzone = 12
	_panel.add_child(_scroll)
	_scroll.add_child(_box)
	music = AudioStreamPlayer.new()
	if ResourceLoader.exists("res://hudba/menu.ogg"):
		var st: AudioStream = load("res://hudba/menu.ogg")
		if st is AudioStreamOggVorbis: (st as AudioStreamOggVorbis).loop = true
		music.stream = st
	music.volume_db = -6.0
	add_child(music)


func _lab(t: String, f: Font, size: int, col: Color) -> Label:
	var l := Label.new()
	l.text = t
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_override("font", f)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("shadow_offset_x", 3)
	l.add_theme_constant_override("shadow_offset_y", 3)
	l.add_theme_constant_override("shadow_outline_size", 6)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


# ------------------------------------------------------------------ úvod

func play_intro() -> void:
	visible = true
	in_game = false
	_intro_t = 0.0
	if music.stream: music.play()
	var tw := create_tween()
	tw.tween_property(_bg, "modulate:a", 1.0, 2.5)
	tw.parallel().tween_property(_title, "modulate:a", 1.0, 3.0).set_delay(1.5)
	tw.parallel().tween_property(_sub, "modulate:a", 1.0, 2.0).set_delay(3.2)
	tw.tween_interval(3.0)
	tw.tween_callback(_end_intro)


func _end_intro() -> void:
	if _intro_t < 0.0:
		return
	_intro_t = -1.0
	_bg.modulate.a = 1.0
	_title.modulate.a = 1.0
	_sub.modulate.a = 1.0
	var tw := create_tween()
	tw.tween_property(_shade, "color:a", 0.35, 0.8)
	show_page("main")


func _input(event: InputEvent) -> void:
	if not visible:
		return
	var pressed: bool = (event is InputEventScreenTouch and event.pressed) or \
			(event is InputEventMouseButton and event.pressed) or \
			(event is InputEventJoypadButton and event.pressed) or \
			(event is InputEventKey and event.pressed)
	if _intro_t >= 0.0 and pressed:
		_end_intro()
		get_viewport().set_input_as_handled()
		return
	# A na ovladači potvrdí tlačítko s fokusem (na některých zařízeních ui_accept A nemá)
	if event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index == JOY_BUTTON_A:
		var f := get_viewport().gui_get_focus_owner()
		if f is Button and not (f as Button).disabled:
			(f as Button).pressed.emit()
			get_viewport().set_input_as_handled()
			return
	if event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index in [JOY_BUTTON_B, JOY_BUTTON_START]:
		_back()
		get_viewport().set_input_as_handled()
	if event is InputEventKey and event.pressed and (event as InputEventKey).keycode == KEY_ESCAPE:
		_back()
		get_viewport().set_input_as_handled()


func _back() -> void:
	if _page != "main":
		show_page("main")
	elif in_game:
		action.emit("resume", null)


# ------------------------------------------------------------------ stránky

func show_menu(game_running: bool) -> void:
	in_game = game_running
	visible = true
	_intro_t = -1.0
	_bg.visible = not game_running
	_bg.modulate.a = 1.0
	_title.modulate.a = 1.0
	_sub.modulate.a = 0.0 if game_running else 1.0
	_shade.color = Color(0, 0, 0, 0.62 if game_running else 0.35)
	show_page("main")


func hide_menu() -> void:
	visible = false
	_panel.visible = false
	if music.playing: music.stop()


func show_page(page: String) -> void:
	_page = page
	for c in _box.get_children():
		_box.remove_child(c)
		c.queue_free()
	_panel.visible = true
	_scroll.scroll_vertical = 0
	var first: Button
	match page:
		"main":
			first = _btn("Pokračovat ve hře" if in_game else "Hrát", "resume" if in_game else "page:play")   # Havran: Hrát → Příběh / Pískoviště
			if in_game:
				_btn("Mapa", "mapa")
				_btn("Místa", "page:mista")
			_btn("Nastavení", "page:settings")
			_btn("Autoři a licence", "page:credits", true)
			_btn("Ukončit", "quit", true)
		"mista":   # rychlé přesuny (dřív v menu hráče Puchartu)
			var ms: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista.json"))["mista"]
			for i in ms.size():
				first = _maybe(first, _btn(String(ms[i]["nazev"]), "misto", false, str(i)))
			_btn("Zpět", "page:main", true)
		"play":   # výběr hry jako v Havranovi (Míša 10. 11.)
			first = _btn("Příběh", "story")
			_btn("Pískoviště", "sandbox")
			_btn("Zpět", "page:main", true)
		"credits":
			for line: String in CREDITS:
				_note(line)
			first = _btn("Zpět", "page:main", true)
		"settings":
			for key: String in ["beh", "let", "obraz"]:
				var bb := _btn(String(settings_text.get(key, key)), "set:" + key, true)
				first = _maybe(first, bb)
			_slider("Hlasitost hudby", "vol:hudba", float(settings_text.get("vol:hudba", 1.0)))
			_btn("Zpět", "page:main", true)
	if first:
		first.call_deferred("grab_focus")


func refresh_settings(texts: Dictionary) -> void:
	settings_text = texts
	if visible and _page == "settings":
		show_page("settings")


func _maybe(cur: Button, b: Button) -> Button:
	return cur if cur else b


func _note(t: String) -> void:
	var l := _lab(t, font_menu, 22 if t.length() < 90 else 19, GOLD_DIM)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 1000.0
	_box.add_child(l)


func _btn(t: String, what: String, small := false, arg: Variant = null) -> Button:
	var b := Button.new()
	b.text = t
	b.custom_minimum_size = Vector2(480, 66 if not small else 56)
	Styl.tlacitko_pruh(b, font_menu, 34 if not small else 28, _box.get_child_count())
	b.pressed.connect(func() -> void: _press(what, arg))
	b.mouse_filter = Control.MOUSE_FILTER_PASS        # tah prstem po tlačítku posouvá menu
	_box.add_child(b)
	_vyska_scroll.call_deferred()
	return b


func _vyska_scroll() -> void:
	var volno := get_viewport().get_visible_rect().size.y - _panel.offset_top - 16.0
	_scroll.custom_minimum_size = Vector2(_box.get_combined_minimum_size().x, minf(_box.get_combined_minimum_size().y, volno))


## Řádek s posuvníkem hlasitosti na pruhu pergamenu (Havran).
func _slider(t: String, what: String, v: float) -> void:
	var row := PanelContainer.new()
	row.add_theme_stylebox_override("panel", Styl.pruh_tlacitko(_box.get_child_count(), "normal"))
	row.custom_minimum_size = Vector2(480, 56)
	row.mouse_filter = Control.MOUSE_FILTER_PASS
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 16)
	row.add_child(h)
	var l := Label.new()
	l.text = t
	l.add_theme_font_override("font", font_menu)
	l.add_theme_font_size_override("font_size", 26)
	l.add_theme_color_override("font_color", Styl.INK)
	l.custom_minimum_size.x = 190
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(l)
	var sl := HSlider.new()
	sl.min_value = 0.0
	sl.max_value = 1.0
	sl.step = 0.05
	sl.value = v
	sl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	sl.custom_minimum_size.y = 32
	var tr := StyleBoxFlat.new()
	tr.bg_color = Color(Styl.INK_SOFT, 0.55)
	tr.content_margin_top = 3
	tr.content_margin_bottom = 3
	tr.set_corner_radius_all(2)
	var fill := tr.duplicate() as StyleBoxFlat
	fill.bg_color = Color(Styl.RED, 0.85)
	sl.add_theme_stylebox_override("slider", tr)
	sl.add_theme_stylebox_override("grabber_area", fill)
	sl.add_theme_stylebox_override("grabber_area_highlight", fill)
	sl.value_changed.connect(func(x: float) -> void: action.emit(what, x))
	h.add_child(sl)
	_box.add_child(row)


func _press(what: String, arg: Variant) -> void:
	if what.begins_with("page:"):
		show_page(what.substr(5))
		return
	action.emit(what, arg)
