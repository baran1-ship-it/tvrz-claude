extends CanvasLayer
## Intro (obraz, hudba, nazev hry) a hlavni menu v gotickem pismu.
## Stranky: hlavni, hrat (Příběh / Pískoviště), nahrat, nastaveni. Stejne menu slouzi i jako pauza ve hre.

signal action(what: String, arg: Variant)

const TITLE := "Odkaz Havrana"
const GOLD := Color(0.93, 0.8, 0.52)
const GOLD_DIM := Color(0.62, 0.53, 0.37)
const TEXT := Color(0.95, 0.9, 0.8)
# autori a licence: jen na teto strance menu, nikde jinde ve hre
const CREDITS := [
	"Hudba (opengameart.org): RandomMind a christislord, CC0; yubatake, CC BY 4.0; marcelofg55, CC BY 3.0; Kevin MacLeod (incompetech.com), CC BY 4.0",
	"Zvuky prostředí, zvířat a předmětů (opengameart.org): gregor-quendel, kurt, thimras, pagdev, qubodup, isaiah658, haeldb, alys, zeroisnotnull, pauliuw, lukerustltd, CC BY; rubberduck, kenney, bart, artisticdude, owlishmedia, medicinestorm, vishwajai, themightyglider, laleksic, tinyworlds, kresiek-the-furry, ignasd, macro a další, CC0 (úplný seznam v zvuky/seznam.txt)",
	"Textury, rostliny, předměty a HDRI: Poly Haven, CC0",
	"Zvuky: Kenney (kenney.nl), CC0",
	"Kroky: congusbongus (z nahrávek swuing, EminYILDIRIM a Ali_6868, freesound.org) a lamoot (Yo Frankie!, Blender Foundation), CC BY 3.0; qubodup, rubberduck, TinyWorlds, Fantozzi, mikeask, peludo, macro, CC0",
	"Figury v erbech: game-icons.net – Lorc a Delapouite, CC BY 3.0",
	"3D modely ze Sketchfabu (CC BY 4.0): AnyRPG (hostinec), Neslihan Çakmak (kupecký stan), Jungle Jim (vybavení krčmy), Thangzy (dveře, kovárna, nářadí), JB3D (zřícené věže), Kevin.Popescu, Kigha, FlukierJupiter, J0Y, wolfgar74, SethSantos, Hineline, AIV, NeverSleep, chaschinkaa, Margot D., Pete.Panousis, LowSeb, Parelaxel, jantonus, LOLIPOP (tráva), naminoff (socha koně ve stáji), MAXDESIGN-3D (kůň)",
	"Kameny, balvany, vozy a keře: vlastní tvorba",
	"Písmo: Grenze Gotisch (Omnibus-Type), SIL Open Font License",
	"Herní engine: Godot Engine, MIT",
]

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
var _scroll: ScrollContainer
var _panel: Control
var _credits: Label
var _help: Control
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
	_sub = _lab("", font_menu, 30, GOLD_DIM)
	_sub.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_sub.offset_top = 156
	_sub.modulate = Color(1, 1, 1, 0)
	add_child(_sub)
	# CenterContainer pres celou plochu pod nadpisem: tlacitka vzdy uprostred obrazovky
	_panel = CenterContainer.new()
	_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	_panel.offset_top = 178
	_panel.offset_bottom = -16
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.visible = false
	add_child(_panel)
	# kazda polozka na vlastnim opalenem pruhu pergamenu
	_box = VBoxContainer.new()
	_box.add_theme_constant_override("separation", 6)
	_box.alignment = BoxContainer.ALIGNMENT_CENTER
	# Misa 0.92: nastaveni se neveslo na tablet a neslo posouvat - posuvna plocha (tahem prstem i pres tlacitka)
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.scroll_deadzone = 12
	_panel.add_child(_scroll)
	_scroll.add_child(_box)
	_credits = _lab("Hudba: Kevin MacLeod (incompetech.com), CC BY 4.0  ·  Textury a rostliny: Poly Haven (CC0)  ·  Zvuky: Kenney, BigSoundBank (CC0)  ·  Písmo: Grenze Gotisch (OFL)",
			font_menu, 18, Color(0.75, 0.7, 0.6, 0.7))
	_credits.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_credits.offset_top = -40
	_credits.visible = false
	add_child(_credits)
	_help = Control.new()
	_help.set_script(load("res://scripts/napoveda.gd"))
	_help.visible = false
	add_child(_help)
	move_child(_help, _panel.get_index())
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
	# A na ovladaci potvrdi tlacitko s fokusem (na nekterych zarizenich ui_accept A nema)
	if event is InputEventJoypadButton and event.pressed and (event as InputEventJoypadButton).button_index == JOY_BUTTON_A:
		var f := get_viewport().gui_get_focus_owner()
		if f is Button and not (f as Button).disabled:
			(f as Button).pressed.emit()
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
	_scroll.scroll_vertical = 0
	_credits.visible = false
	_help.visible = page == "help"
	_title.visible = page != "help"
	_panel.offset_top = 178 if page != "help" else get_viewport().get_visible_rect().size.y - 150
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
			_btn("Nápověda", "page:help")
			_btn("Autoři a licence", "page:credits", true)
		"play":
			first = _btn("Příběh", "story")
			_btn("Pískoviště", "sandbox")
			_btn("Zpět", "page:main", true)
		"load":
			for sv: Dictionary in saves.slice(0, 7):
				var bb := _btn(String(sv["label"]), "load", false, sv["file"])
				first = _maybe(first, bb)
			first = _maybe(first, _btn("Zpět", "page:main", true))
		"help":
			first = _btn("Zpět", "page:main", true)
		"credits":
			for line: String in CREDITS:
				_note(line)
			first = _btn("Zpět", "page:main", true)
		"settings":
			for key: String in ["mereni", "log", "quality", "sens", "pohyb", "kun", "music", "vol:hudba", "zvuky", "vol:zvuky", "msaa", "plne_3d", "fyzika", "test_pameti", "time"]:
				if key == "time" and not in_game:
					continue
				if key.begins_with("vol:"):
					_slider("Hlasitost hudby" if key == "vol:hudba" else "Hlasitost zvuků", key, float(settings_text.get(key, 1.0)))
					continue
				var bb2 := _btn(String(settings_text.get(key, key)), "set:" + key, true)
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
	var l := _lab(t, font_menu, 22 if t.length() < 90 else 19, GOLD_DIM)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART           # dlouhe radky (autori modelu) se zalomi
	l.custom_minimum_size.x = 1000.0
	_box.add_child(l)


func _btn(t: String, what: String, small := false, arg: Variant = null) -> Button:
	var b := Button.new()
	b.text = t
	b.custom_minimum_size = Vector2(480, 66 if not small else 56)
	Styl.tlacitko_pruh(b, font_menu, 34 if not small else 28, _box.get_child_count())
	b.pressed.connect(func() -> void: _press(what, arg))
	b.mouse_filter = Control.MOUSE_FILTER_PASS        # tah prstem po tlacitku posouva menu
	_box.add_child(b)
	_vyska_scroll.call_deferred()
	return b


## Vyska posuvne plochy = obsah, nejvys volne misto pod nadpisem (CenterContainer ji pak vystredi).
func _vyska_scroll() -> void:
	var volno := get_viewport().get_visible_rect().size.y - _panel.offset_top - 16.0
	_scroll.custom_minimum_size = Vector2(_box.get_combined_minimum_size().x, minf(_box.get_combined_minimum_size().y, volno))


## Radek s posuvnikem hlasitosti na pruhu pergamenu (dotyk, mys, ovladac vlevo/vpravo).
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
	var tr := StyleBoxFlat.new()                      # draha: inkoustova linka
	tr.bg_color = Color(Styl.INK_SOFT, 0.55)
	tr.content_margin_top = 3
	tr.content_margin_bottom = 3
	tr.set_corner_radius_all(2)
	var fill := tr.duplicate() as StyleBoxFlat        # vyplnena cast: cerveny inkoust
	fill.bg_color = Color(Styl.RED, 0.85)
	sl.add_theme_stylebox_override("slider", tr)
	sl.add_theme_stylebox_override("grabber_area", fill)
	sl.add_theme_stylebox_override("grabber_area_highlight", fill)
	var foc := StyleBoxFlat.new()
	foc.draw_center = false
	foc.border_color = Color(Styl.RED, 0.6)
	foc.set_border_width_all(2)
	foc.set_corner_radius_all(6)
	sl.add_theme_stylebox_override("focus", foc)
	var pec := _pecet_ikona()
	sl.add_theme_icon_override("grabber", pec)
	sl.add_theme_icon_override("grabber_highlight", pec)
	sl.value_changed.connect(func(x: float) -> void: action.emit(what, x))
	h.add_child(sl)
	var pad := Control.new()
	pad.custom_minimum_size.x = 6
	h.add_child(pad)
	_box.add_child(row)


var _pecet_tex: Texture2D


## Bezec posuvniku: mala voskova pecet (kreslena do obrazku jednou).
func _pecet_ikona() -> Texture2D:
	if _pecet_tex:
		return _pecet_tex
	var n := 36
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var c := Vector2(n, n) * 0.5
	for y in n:
		for x in n:
			var d := Vector2(x + 0.5, y + 0.5).distance_to(c)
			var a := atan2(y + 0.5 - c.y, x + 0.5 - c.x)
			var r := n * 0.46 * (1.0 + 0.06 * sin(a * 5.0 + 1.3))
			if d < r:
				var k := 1.0 if d < r * 0.72 else 0.82
				var col := Color(0.62, 0.1, 0.06) * k
				if absf(d - r * 0.72) < 1.0:
					col = Color(0.36, 0.04, 0.02)
				col.a = clampf(r - d, 0.0, 1.0)
				img.set_pixel(x, y, col)
	_pecet_tex = ImageTexture.create_from_image(img)
	return _pecet_tex


func _press(what: String, arg: Variant) -> void:
	if what.begins_with("page:"):
		show_page(what.substr(5))
		return
	action.emit(what, arg)
