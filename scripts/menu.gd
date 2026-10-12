extends CanvasLayer
## Intro (obraz, hudba, nazev hry) a hlavni menu v gotickem pismu.
## Stranky: hlavni, hrat (Příběh / Pískoviště), nahrat, nastaveni. Stejne menu slouzi i jako pauza ve hre.

signal action(what: String, arg: Variant)

const TITLE := "Odkaz Havrana"
const GOLD := Color(0.93, 0.8, 0.52)
const GOLD_DIM := Color(0.62, 0.53, 0.37)
const TEXT := Color(0.95, 0.9, 0.8)

var font_title: FontFile
var font_menu: FontFile
var in_game := false            # bezi hra: menu je pauza
var can_save := false
var saves: Array = []           # [{file, label}] nejnovejsi prvni
var settings_text: Dictionary = {}

var _bg: TextureRect
var _shade: ColorRect
var _title: Label
var _sub: Label
var _box: VBoxContainer
var _panel: Control
var _credits: Label
var _intro_t := -1.0
var _page := "main"
var music: AudioStreamPlayer


func _ready() -> void:
	layer = 20
	process_mode = Node.PROCESS_MODE_ALWAYS
	font_title = load("res://fonts/GrenzeGotisch-Bold.ttf")
	font_menu = load("res://fonts/GrenzeGotisch-Medium.ttf")
	_bg = TextureRect.new()
	_bg.texture = load("res://obrazky/intro.jpg")
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
	_title.offset_top = 36
	_title.modulate = Color(1, 1, 1, 0)
	add_child(_title)
	_sub = _lab("Léta Páně 1403, kraj pod Sázavou", font_menu, 30, GOLD_DIM)
	_sub.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_sub.offset_top = 156
	_sub.modulate = Color(1, 1, 1, 0)
	add_child(_sub)
	# CenterContainer pres celou plochu pod nadpisem: tlacitka vzdy uprostred obrazovky
	_panel = CenterContainer.new()
	_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.offset_top = 200
	_panel.offset_bottom = -44
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.visible = false
	add_child(_panel)
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 8)
	_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_panel.add_child(_box)
	_credits = _lab("Hudba: Kevin MacLeod (incompetech.com), CC BY 4.0  ·  Textury a rostliny: Poly Haven (CC0)  ·  Písmo: Grenze Gotisch (OFL)",
			font_menu, 18, Color(0.75, 0.7, 0.6, 0.7))
	_credits.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_credits.offset_top = -40
	_credits.visible = false
	add_child(_credits)
	music = AudioStreamPlayer.new()
	var st: AudioStream = load("res://hudba/menu.ogg")
	if st is AudioStreamOggVorbis:
		(st as AudioStreamOggVorbis).loop = true
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


# ------------------------------------------------------------------ intro

func play_intro() -> void:
	visible = true
	in_game = false
	_intro_t = 0.0
	music.play()
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
	tw.tween_property(_shade, "color:a", 0.45, 0.8)
	tw.parallel().tween_property(_sub, "modulate:a", 0.0, 0.6)
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
	if event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index == JOY_BUTTON_B:
		_back()
		get_viewport().set_input_as_handled()


func _back() -> void:
	if _page != "main":
		show_page("main")
	elif in_game:
		action.emit("resume", null)


# ------------------------------------------------------------------ stranky menu

func show_menu(game_running: bool, saving_allowed: bool) -> void:
	in_game = game_running
	can_save = saving_allowed
	visible = true
	_intro_t = -1.0
	_bg.visible = not game_running
	_bg.modulate.a = 1.0
	_title.modulate.a = 1.0
	_sub.modulate.a = 0.0
	_shade.color = Color(0, 0, 0, 0.62 if game_running else 0.45)
	show_page("main")


func hide_menu() -> void:
	visible = false
	_panel.visible = false


func show_page(page: String) -> void:
	_page = page
	for c in _box.get_children():
		_box.remove_child(c)
		c.queue_free()
	_panel.visible = true
	_credits.visible = page == "main" and not in_game
	var first: Button
	match page:
		"main":
			if in_game:
				first = _btn("Pokračovat ve hře", "resume")
			first = _maybe(first, _btn("Hrát", "page:play"))
			if not in_game and not saves.is_empty():
				_btn("Pokračovat", "continue")
			var b := _btn("Nahrát", "page:load")
			b.disabled = saves.is_empty()
			var s := _btn("Uložit", "save")
			s.disabled = not can_save
			_btn("Nastavení", "page:settings")
			_btn("Uložit a ukončit" if can_save else "Ukončit", "save_quit")
		"play":
			first = _btn("Příběh", "story")
			_btn("Pískoviště", "sandbox")
			_note("Pískoviště: volné procházení, skákání a létání\n(dvakrát rychle skoč)")
			_btn("Zpět", "page:main", true)
		"load":
			for sv: Dictionary in saves.slice(0, 7):
				var bb := _btn(String(sv["label"]), "load", false, sv["file"])
				first = _maybe(first, bb)
			first = _maybe(first, _btn("Zpět", "page:main", true))
		"settings":
			for key: String in ["quality", "sens", "music", "time"]:
				if key == "time" and not in_game:
					continue
				var bb2 := _btn(String(settings_text.get(key, key)), "set:" + key)
				first = _maybe(first, bb2)
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
	var l := _lab(t, font_menu, 22, GOLD_DIM)
	_box.add_child(l)


func _btn(t: String, what: String, small := false, arg: Variant = null) -> Button:
	var b := Button.new()
	b.text = t
	b.custom_minimum_size = Vector2(500, 58 if not small else 50)
	b.add_theme_font_override("font", font_menu)
	b.add_theme_font_size_override("font_size", 36 if not small else 30)
	b.add_theme_color_override("font_color", TEXT)
	b.add_theme_color_override("font_hover_color", GOLD)
	b.add_theme_color_override("font_focus_color", GOLD)
	b.add_theme_color_override("font_pressed_color", GOLD)
	b.add_theme_color_override("font_disabled_color", Color(0.55, 0.5, 0.45, 0.6))
	var n := StyleBoxFlat.new()
	n.bg_color = Color(0.08, 0.06, 0.045, 0.72)
	n.border_color = Color(0.55, 0.43, 0.25, 0.8)
	n.set_border_width_all(2)
	n.set_corner_radius_all(4)
	n.set_content_margin_all(6)
	var h := n.duplicate() as StyleBoxFlat
	h.bg_color = Color(0.2, 0.14, 0.08, 0.85)
	h.border_color = GOLD
	var f := h.duplicate() as StyleBoxFlat
	f.set_border_width_all(3)
	var d := n.duplicate() as StyleBoxFlat
	d.bg_color = Color(0.06, 0.05, 0.04, 0.5)
	d.border_color = Color(0.35, 0.3, 0.22, 0.5)
	b.add_theme_stylebox_override("normal", n)
	b.add_theme_stylebox_override("hover", h)
	b.add_theme_stylebox_override("pressed", h)
	b.add_theme_stylebox_override("focus", f)
	b.add_theme_stylebox_override("disabled", d)
	b.pressed.connect(func() -> void: _press(what, arg))
	_box.add_child(b)
	return b


func _press(what: String, arg: Variant) -> void:
	if what.begins_with("page:"):
		show_page(what.substr(5))
		return
	action.emit(what, arg)
