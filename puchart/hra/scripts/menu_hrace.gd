extends CanvasLayer
## Menu hráče (Míša 9. 11.: „hráčovo jako v Havranovi“; rozhodnutí: vzhled Havrana, obsah Puchartu): pergamen s pruhy
## stránek nahoře (LB/RB nebo dotyk), stránky Mapa, Místa (přesun), Deník (hra/data/denik.json – jen doložené údaje).
## Brašna a Dovednosti přibudou s inventářem. Otevírá ikona erbu vlevo nahoře nebo kříž dolů na ovladači.

const GOLD := Color(0.89, 0.73, 0.41)
const STRANKY := [["mapa", "Mapa"], ["mista", "Místa"], ["denik", "Deník"]]

var proch: Node                 # prochazka.gd (mapa, přesun)
var open := false
var _str := 2
var _fb: Font
var _fm: Font
var _list: PanelContainer
var _tabs: HBoxContainer
var _obsah: VBoxContainer
var _scroll: ScrollContainer
var _nadpis: Label
var _denik: Array = []


func _ready() -> void:
	layer = 18
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	_fb = load("res://fonty/GrenzeGotisch-Bold.ttf")
	_fm = load("res://fonty/GrenzeGotisch-Medium.ttf")
	if FileAccess.file_exists("res://data/denik.json"):
		_denik = JSON.parse_string(FileAccess.get_file_as_string("res://data/denik.json"))["zapisy"]
	var stin := ColorRect.new(); stin.color = Color(0, 0, 0, 0.55); stin.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(stin)
	var cc := CenterContainer.new(); cc.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(cc)
	_list = Styl.panel(48.0)
	var vp := get_viewport().get_visible_rect().size
	_list.custom_minimum_size = Vector2(minf(1100.0, vp.x - 80.0), minf(820.0, vp.y - 60.0))
	cc.add_child(_list)
	var v := VBoxContainer.new(); v.add_theme_constant_override("separation", 10); _list.add_child(v)
	_nadpis = Label.new(); _nadpis.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_nadpis.add_theme_font_override("font", _fb); _nadpis.add_theme_font_size_override("font_size", 46)
	_nadpis.add_theme_color_override("font_color", Styl.INK)
	v.add_child(_nadpis)
	_tabs = HBoxContainer.new(); _tabs.alignment = BoxContainer.ALIGNMENT_CENTER; _tabs.add_theme_constant_override("separation", 12)
	v.add_child(_tabs)
	for i in STRANKY.size():
		var b := Button.new(); b.text = STRANKY[i][1]; b.custom_minimum_size = Vector2(220, 58)
		Styl.tlacitko_pruh(b, _fm, 30, i)
		b.pressed.connect(func() -> void: ukaz(i))
		_tabs.add_child(b)
	_scroll = ScrollContainer.new(); _scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED; _scroll.scroll_deadzone = 12
	v.add_child(_scroll)
	_obsah = VBoxContainer.new(); _obsah.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_obsah.add_theme_constant_override("separation", 8)
	_scroll.add_child(_obsah)
	var zav := Button.new(); zav.text = "Zavřít"; zav.custom_minimum_size = Vector2(260, 56)
	Styl.tlacitko_pruh(zav, _fm, 28, 3); zav.pressed.connect(zavri)
	var zc := CenterContainer.new(); zc.add_child(zav); v.add_child(zc)


func otevri() -> void:
	open = true; visible = true
	get_tree().paused = true
	ukaz(_str)


func zavri() -> void:
	open = false; visible = false
	get_tree().paused = false
	var f := get_viewport().gui_get_focus_owner()
	if f: f.release_focus()


func ukaz(i: int) -> void:
	_str = posmod(i, STRANKY.size())
	_nadpis.text = {"mapa": "Mapa panství", "mista": "Místa", "denik": "Deník"}[STRANKY[_str][0]]
	for k in _tabs.get_child_count():
		(_tabs.get_child(k) as Button).modulate = Color(1, 1, 1, 1.0 if k == _str else 0.6)
	for c in _obsah.get_children():
		_obsah.remove_child(c); c.queue_free()
	_scroll.scroll_vertical = 0
	var prvni: Button
	match STRANKY[_str][0]:
		"mapa":
			_text("Ručně kreslená mapa okolí Puchartu: oba hrady, cesty údolím Veličky a k Potštátu, mosty a brody.")
			prvni = _tl("Otevřít mapu", func() -> void: zavri(); proch.mapa.prepni())
		"mista":
			for m in proch.mista:
				var b := _tl(String(m["nazev"]), func() -> void: zavri(); proch._presun(m))
				if prvni == null: prvni = b
		"denik":
			for z in _denik:
				_text(String(z["nadpis"]), true)
				_text(String(z["text"]))
	if prvni: prvni.call_deferred("grab_focus")
	else: (_tabs.get_child(_str) as Button).call_deferred("grab_focus")


func _tl(t: String, f: Callable) -> Button:
	var b := Button.new(); b.text = t; b.custom_minimum_size = Vector2(520, 56)
	Styl.tlacitko_pruh(b, _fm, 28, _obsah.get_child_count())
	b.pressed.connect(f); b.mouse_filter = Control.MOUSE_FILTER_PASS
	var cc := CenterContainer.new(); cc.add_child(b); _obsah.add_child(cc)
	return b


func _text(t: String, nadpis := false) -> void:
	var l := Label.new(); l.text = t; l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_override("font", _fb if nadpis else _fm)
	l.add_theme_font_size_override("font_size", 32 if nadpis else 26)
	l.add_theme_color_override("font_color", Styl.RED if nadpis else Styl.INK)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_obsah.add_child(l)


func _input(e: InputEvent) -> void:
	if not open: return
	if e is InputEventJoypadButton and e.pressed:
		match (e as InputEventJoypadButton).button_index:
			JOY_BUTTON_B, JOY_BUTTON_DPAD_DOWN: zavri()
			JOY_BUTTON_LEFT_SHOULDER: ukaz(_str - 1)
			JOY_BUTTON_RIGHT_SHOULDER: ukaz(_str + 1)
			JOY_BUTTON_A:
				var f := get_viewport().gui_get_focus_owner()
				if f is Button: (f as Button).pressed.emit()
			_: return
		get_viewport().set_input_as_handled()
	elif e is InputEventKey and e.pressed and (e as InputEventKey).keycode in [KEY_ESCAPE, KEY_TAB]:
		zavri(); get_viewport().set_input_as_handled()
