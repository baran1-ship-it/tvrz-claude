extends CanvasLayer
## Dotykove ovladani a ukazatele. Vlevo plovouci packa pro chuzi, vpravo tazenim rozhlizeni,
## tlacitka kreslena primo (bez Control uzlu), aby slo ovladat vic prsty naraz.

signal use_pressed
signal use2_pressed
signal menu_action(what: String)

const STICK_R := 74.0
const KNOB_R := 30.0

var player: CharacterBody3D
var bow: Node
var sens := 1.0
var gamepad := false          # hraje se ovladacem: dotykove prvky se skryji

var _root: Control
var _pad: Control
var _menu: Control
var _menu_btns: Dictionary = {}
var _fps: Label
var _loading: Control
var _loading_text: Label
var _bag_tex: Texture2D
var _build_tex: Texture2D
var can_build := false
var _fade: ColorRect
var _font: Font

var _stick_id := -1
var _look_id := -1
var _draw_id := -1
var _jump_id := -1
var _down_id := -1
var _stick_o := Vector2.ZERO
var _stick_v := Vector2.ZERO
var _look_last := Vector2.ZERO
var _draw_last := Vector2.ZERO

var use_text := ""
var build_mode := false
var use_text2 := ""            # druha akce (X): presunout predmet
var _scroll_t := 0.0
var _scroll_text := ""
var _scroll_tex: Texture2D
var _gothic: Font
var _place := ""
var _place_t := 0.0
var _toast := ""
var _toast_t := 0.0
var _score_line := ""
var paused := false


func _ready() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_font = ThemeDB.fallback_font
	_scroll_tex = load("res://obrazky/pergamen.png")
	_gothic = load("res://fonts/GrenzeGotisch-Medium.ttf")
	_pad = Control.new()
	_pad.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_pad.draw.connect(_draw_pad)
	_root.add_child(_pad)
	_build_menu()
	_fade = ColorRect.new()
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_fade)
	_build_loading()


func _size() -> Vector2:
	return _root.get_rect().size


# ------------------------------------------------------------------ nacitani a prolinani

func _build_loading() -> void:
	_loading = ColorRect.new()
	(_loading as ColorRect).color = Color(0.035, 0.033, 0.03)
	_loading.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(_loading)
	var cc := CenterContainer.new()
	cc.set_anchors_preset(Control.PRESET_FULL_RECT)
	_loading.add_child(cc)
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	cc.add_child(v)
	var t := _label("Odkaz Havrana", 84, Color(0.93, 0.8, 0.52))
	t.add_theme_font_override("font", load("res://fonts/GrenzeGotisch-Bold.ttf"))
	v.add_child(t)
	var t2 := _label("Načítám tvrz…", 30, Color(0.7, 0.62, 0.48))
	t2.add_theme_font_override("font", load("res://fonts/GrenzeGotisch-Medium.ttf"))
	v.add_child(t2)
	_loading_text = t2


func loading_status(t: String) -> void:
	if _loading_text:
		_loading_text.text = t


func hide_loading() -> void:
	var tw := create_tween()
	tw.tween_property(_loading, "modulate:a", 0.0, 0.8)
	tw.tween_callback(_loading.hide)


func fade_through(mid: Callable, hold: float = 0.8) -> void:
	var tw := create_tween()
	tw.tween_property(_fade, "color:a", 1.0, 0.9)
	tw.tween_callback(mid)
	tw.tween_interval(hold)
	tw.tween_property(_fade, "color:a", 0.0, 1.2)


func _label(t: String, size: int, col: Color) -> Label:
	var l := Label.new()
	l.text = t
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	return l


# ------------------------------------------------------------------ menu

func _build_menu() -> void:
	_menu = ColorRect.new()
	(_menu as ColorRect).color = Color(0.02, 0.02, 0.02, 0.62)
	_menu.set_anchors_preset(Control.PRESET_FULL_RECT)
	_menu.visible = false
	_root.add_child(_menu)
	var panel := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.11, 0.095, 0.08, 0.94)
	sb.border_color = Color(0.55, 0.45, 0.3)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(10)
	sb.set_content_margin_all(26)
	panel.add_theme_stylebox_override("panel", sb)
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.custom_minimum_size = Vector2(460, 0)
	panel.position = Vector2(-230, -230)
	_menu.add_child(panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 12)
	panel.add_child(v)
	v.add_child(_label("Tvrz", 44, Color(0.93, 0.86, 0.7)))
	for key: String in ["resume", "time", "quality", "sens", "quit"]:
		var b := Button.new()
		b.custom_minimum_size = Vector2(400, 58)
		b.add_theme_font_size_override("font_size", 24)
		var n := StyleBoxFlat.new()
		n.bg_color = Color(0.22, 0.18, 0.14)
		n.set_corner_radius_all(8)
		var h := n.duplicate() as StyleBoxFlat
		h.bg_color = Color(0.33, 0.26, 0.18)
		b.add_theme_stylebox_override("normal", n)
		b.add_theme_stylebox_override("hover", n)
		b.add_theme_stylebox_override("pressed", h)
		var fo := StyleBoxFlat.new()
		fo.draw_center = false
		fo.border_color = Color(1.0, 0.85, 0.5)
		fo.set_border_width_all(3)
		fo.set_corner_radius_all(8)
		b.add_theme_stylebox_override("focus", fo)
		b.add_theme_color_override("font_color", Color(0.95, 0.9, 0.8))
		b.pressed.connect(func() -> void: menu_action.emit(key))
		v.add_child(b)
		_menu_btns[key] = b
	_fps = _label("", 16, Color(0.6, 0.56, 0.5))
	v.add_child(_fps)


func set_menu_text(key: String, t: String) -> void:
	if _menu_btns.has(key):
		(_menu_btns[key] as Button).text = t


func show_menu(on: bool) -> void:
	paused = on
	_menu.visible = on
	_release_all()
	if on and gamepad:
		focus_menu()


func focus_menu() -> void:
	if _menu_btns.has("resume"):
		(_menu_btns["resume"] as Button).grab_focus()


# ------------------------------------------------------------------ oznameni

func show_place(t: String) -> void:
	_place = t
	_place_t = 3.2


func toast(t: String, secs: float = 2.0) -> void:
	_toast = t
	_toast_t = secs


func set_score_line(t: String) -> void:
	_score_line = t


# ------------------------------------------------------------------ rozlozeni tlacitek

func _btn_menu() -> Rect2:
	var s := _size()
	return Rect2(s.x - 86, 18, 68, 60)


func _btn_use2() -> Rect2:
	var r := _btn_use()
	return Rect2(r.position + Vector2(40, r.size.y + 14), Vector2(r.size.x - 80, r.size.y - 10))


func _btn_build() -> Rect2:
	var s := _size()
	return Rect2(s.x - 254, 14, 68, 68)


func _btn_bag() -> Rect2:
	var s := _size()
	return Rect2(s.x - 170, 14, 68, 68)


func _btn_use() -> Rect2:
	var s := _size()
	return Rect2(s.x - 330, s.y * 0.5 - 40, 300, 72)


func _draw_center() -> Vector2:
	var s := _size()
	return Vector2(s.x - 140, s.y - 150)


func _jump_center() -> Vector2:
	var s := _size()
	if bow and bow.equipped:
		return Vector2(s.x - 290, s.y - 90)
	return Vector2(s.x - 120, s.y - 120)


func _down_center() -> Vector2:
	return _jump_center() + Vector2(-110, 30)


func _stick_home() -> Vector2:
	var s := _size()
	return Vector2(150, s.y - 150)


# ------------------------------------------------------------------ dotyk

func _input(event: InputEvent) -> void:
	if paused or player == null or _loading.visible:
		return
	if event is InputEventScreenTouch:
		var e := event as InputEventScreenTouch
		if e.pressed:
			_touch_down(e.index, e.position)
		else:
			_touch_up(e.index)
	elif event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		_touch_move(d.index, d.position)


func _touch_down(id: int, p: Vector2) -> void:
	var s := _size()
	if _btn_menu().grow(14).has_point(p):
		menu_action.emit("open")
		return
	if _btn_bag().grow(8).has_point(p):
		menu_action.emit("brasna")
		return
	if can_build and _btn_build().grow(8).has_point(p):
		menu_action.emit("stavba")
		return
	if use_text2 != "" and _btn_use2().grow(8).has_point(p):
		use2_pressed.emit()
		return
	if use_text != "" and _btn_use().grow(10).has_point(p):
		use_pressed.emit()
		return
	if p.distance_to(_jump_center()) < 58.0:
		player.jump()
		player.fly_up = true
		_jump_id = id
		return
	if player.flying and p.distance_to(_down_center()) < 52.0:
		player.fly_down = true
		_down_id = id
		return
	if bow and bow.equipped and _draw_id == -1 and p.distance_to(_draw_center()) < 96.0:
		_draw_id = id
		_draw_last = p
		bow.begin_draw()
		return
	if p.x < s.x * 0.42 and _stick_id == -1:
		_stick_id = id
		_stick_o = p
		_stick_v = Vector2.ZERO
		return
	if _look_id == -1:
		_look_id = id
		_look_last = p


func _touch_move(id: int, p: Vector2) -> void:
	if id == _stick_id:
		var v := (p - _stick_o) / STICK_R
		if v.length() > 1.0:
			# packa se nechava tahnout za prstem
			_stick_o = p - v.normalized() * STICK_R
			v = v.normalized()
		_stick_v = v
		var dead := 0.12
		var m := v.length()
		var out := Vector2.ZERO if m < dead else v.normalized() * ((m - dead) / (1.0 - dead))
		player.move_input = Vector2(out.x, -out.y)
	elif id == _look_id:
		_look(p - _look_last)
		_look_last = p
	elif id == _draw_id:
		_look(p - _draw_last)
		_draw_last = p


func _look(d: Vector2) -> void:
	var k := 0.0042 * sens
	if bow and bow.drawing:
		k *= 0.6
	player.look(d.x * k, d.y * k)


func _touch_up(id: int) -> void:
	if id == _jump_id:
		_jump_id = -1
		player.fly_up = false
	elif id == _down_id:
		_down_id = -1
		player.fly_down = false
	elif id == _stick_id:
		_stick_id = -1
		_stick_v = Vector2.ZERO
		player.move_input = Vector2.ZERO
	elif id == _look_id:
		_look_id = -1
	elif id == _draw_id:
		_draw_id = -1
		bow.release()


func _release_all() -> void:
	_jump_id = -1
	_down_id = -1
	if player:
		player.fly_up = false
		player.fly_down = false
	_stick_id = -1
	_look_id = -1
	if _draw_id != -1 and bow:
		bow.release()
	_draw_id = -1
	_stick_v = Vector2.ZERO
	if player:
		player.move_input = Vector2.ZERO


# ------------------------------------------------------------------ kresleni

func _process(delta: float) -> void:
	# pergamen s akci se rozbali (0 -> 1), pri zmene textu znovu
	if use_text == "":
		_scroll_t = 0.0
	else:
		if use_text != _scroll_text:
			_scroll_text = use_text
			_scroll_t = 0.0
		_scroll_t = minf(1.0, _scroll_t + delta / 0.28)
	if _place_t > 0.0:
		_place_t -= delta
	if _toast_t > 0.0:
		_toast_t -= delta
	if paused:
		_fps.text = "%d snímků za sekundu" % Engine.get_frames_per_second()
	_pad.queue_redraw()


func _text(pos: Vector2, t: String, size: int, col: Color, align := HORIZONTAL_ALIGNMENT_CENTER, width := -1.0) -> void:
	var w := width if width > 0.0 else 1000.0
	var x := pos.x - w * 0.5 if align == HORIZONTAL_ALIGNMENT_CENTER else pos.x
	_pad.draw_string(_font, Vector2(x + 2, pos.y + 2), t, align, w, size, Color(0, 0, 0, col.a * 0.55))
	_pad.draw_string(_font, Vector2(x, pos.y), t, align, w, size, col)


func _draw_pad() -> void:
	if player == null or paused or _loading.visible:
		return
	var s := _size()
	var c := s * 0.5
	# zamerovaci tecka
	if bow and bow.equipped:
		var g: float = 6.0 + 10.0 * (1.0 - bow.draw)
		var col := Color(1, 1, 1, 0.55 + 0.4 * float(bow.draw))
		_pad.draw_line(c + Vector2(-g - 8, 0), c + Vector2(-g, 0), col, 2.0)
		_pad.draw_line(c + Vector2(g, 0), c + Vector2(g + 8, 0), col, 2.0)
		_pad.draw_line(c + Vector2(0, -g - 8), c + Vector2(0, -g), col, 2.0)
		_pad.draw_line(c + Vector2(0, g), c + Vector2(0, g + 8), col, 2.0)
	else:
		_pad.draw_circle(c, 2.6, Color(1, 1, 1, 0.6))
	if gamepad:
		_draw_gamepad_hints(s, c)
		return
	# packa
	var home := _stick_o if _stick_id != -1 else _stick_home()
	_pad.draw_circle(home, STICK_R, Color(1, 1, 1, 0.08 if _stick_id == -1 else 0.14))
	_pad.draw_arc(home, STICK_R, 0, TAU, 48, Color(1, 1, 1, 0.3), 2.0, true)
	_pad.draw_circle(home + _stick_v * STICK_R, KNOB_R, Color(1, 1, 1, 0.28 if _stick_id == -1 else 0.5))
	# skok
	var jc := _jump_center()
	_pad.draw_circle(jc, 40, Color(0, 0, 0, 0.25))
	_pad.draw_arc(jc, 40, 0, TAU, 40, Color(1, 1, 1, 0.45), 2.0, true)
	_pad.draw_polyline(PackedVector2Array([jc + Vector2(-12, 6), jc + Vector2(0, -8), jc + Vector2(12, 6)]), Color(1, 1, 1, 0.8), 3.0, true)
	if player.flying:
		var dc2 := _down_center()
		_pad.draw_circle(dc2, 36, Color(0, 0, 0, 0.25))
		_pad.draw_arc(dc2, 36, 0, TAU, 40, Color(1, 1, 1, 0.45), 2.0, true)
		_pad.draw_polyline(PackedVector2Array([dc2 + Vector2(-12, -6), dc2 + Vector2(0, 8), dc2 + Vector2(12, -6)]), Color(1, 1, 1, 0.8), 3.0, true)
		_text(Vector2(jc.x - 40, jc.y - 64), "Let – dvojklepnutím vypneš", 18, Color(1, 0.95, 0.8, 0.8))
	# luk
	if bow and bow.equipped:
		var dc := _draw_center()
		var on: bool = bow.drawing
		_pad.draw_circle(dc, 82, Color(0.55, 0.12, 0.08, 0.45 if on else 0.3))
		_pad.draw_arc(dc, 82, 0, TAU, 56, Color(1, 0.9, 0.75, 0.6), 2.5, true)
		if bow.draw > 0.0:
			_pad.draw_arc(dc, 90, -PI * 0.5, -PI * 0.5 + TAU * bow.draw, 56, Color(1.0, 0.85, 0.4, 0.9), 6.0, true)
		_text(dc + Vector2(0, 9), "Napnout" if not on else ("Pusť!" if bow.draw >= 1.0 else "Drž…"), 24, Color(1, 0.95, 0.85, 0.95))
		_text(Vector2(s.x - 24, 112), _score_line, 22, Color(1, 0.93, 0.75, 0.95), HORIZONTAL_ALIGNMENT_RIGHT, 0.0)
	# menu
	var mr := _btn_menu()
	_pad.draw_rect(mr, Color(0, 0, 0, 0.3))
	for k in 3:
		_pad.draw_rect(Rect2(mr.position + Vector2(18, 16 + k * 12), Vector2(32, 4)), Color(1, 1, 1, 0.8))
	# brasna: erb se lvem
	if _bag_tex == null:
		_bag_tex = load("res://obrazky/erby/vse.png")
	_pad.draw_texture_rect(_bag_tex, _btn_bag(), false, Color(1, 1, 1, 0.85))
	if can_build:
		if _build_tex == null:
			_build_tex = load("res://obrazky/erby/remeslo.png")
		var br := _btn_build()
		if build_mode:
			_pad.draw_circle(br.get_center(), 40, Color(1.0, 0.8, 0.4, 0.35))
		_pad.draw_texture_rect(_build_tex, br, false, Color(1, 1, 1, 0.95 if build_mode else 0.7))
	if build_mode:
		_text(Vector2(_size().x * 0.5, 50), "Stavební režim", 36, Color(1, 0.86, 0.5, 0.95))
	# pouziti: rozbalovaci pergamen (klepnutim se provede)
	if use_text != "":
		_draw_scroll(_btn_use(), use_text, false)
	if use_text2 != "":
		_draw_scroll(_btn_use2(), use_text2, false)
	# misto a zpravy
	if _place_t > 0.0:
		var a := clampf(_place_t, 0.0, 1.0)
		_text(Vector2(c.x, 62), _place, 34, Color(0.97, 0.92, 0.8, a))
	if _toast_t > 0.0:
		var a2 := clampf(_toast_t / 0.4, 0.0, 1.0)
		_text(Vector2(c.x, s.y * 0.68), _toast, 30, Color(1, 0.9, 0.62, a2))


## Pergamen: rozbali se od stredu do stran, gotickym pismem text akce, u ovladace odznak A.
func _draw_scroll(r: Rect2, t: String, pad_hint: bool, letter := "A") -> void:
	var k := _scroll_t * _scroll_t * (3.0 - 2.0 * _scroll_t)
	var w := maxf(r.size.y * 0.5, r.size.x * k)
	var rr := Rect2(r.position.x + (r.size.x - w) * 0.5, r.position.y, w, r.size.y)
	_pad.draw_texture_rect(_scroll_tex, rr, false, Color(1, 1, 1, 0.97))
	if k < 0.6:
		return
	var a := clampf((k - 0.6) / 0.4, 0.0, 1.0)
	var tx := rr.position.x + (34.0 if pad_hint else 0.0)
	var tw := rr.size.x - (34.0 if pad_hint else 0.0)
	_pad.draw_string(_gothic, Vector2(tx, rr.position.y + rr.size.y * 0.5 + 12), t, HORIZONTAL_ALIGNMENT_CENTER, tw, 34,
			Color(0.24, 0.14, 0.07, a))
	if pad_hint:
		var cpos := rr.position + Vector2(48, rr.size.y * 0.5)
		_pad.draw_circle(cpos, 19, Color(0.18, 0.42, 0.16, a) if letter == "A" else Color(0.15, 0.3, 0.7, a))
		_pad.draw_arc(cpos, 19, 0, TAU, 24, Color(0.92, 0.85, 0.6, a), 2.0, true)
		_pad.draw_string(_font, cpos + Vector2(-20, 8), letter, HORIZONTAL_ALIGNMENT_CENTER, 40, 22, Color(1, 1, 1, a))


func _draw_gamepad_hints(s: Vector2, c: Vector2) -> void:
	if build_mode:
		_text(Vector2(c.x, 50), "Stavební režim", 36, Color(1, 0.86, 0.5, 0.95))
		_text(Vector2(c.x, 86), "A přesunout · X odstranit · D-pad dolů katalog · B konec", 22, Color(1, 0.93, 0.75, 0.85))
	if use_text != "":
		_draw_scroll(Rect2(s.x * 0.5 - 190, s.y * 0.62, 380, 82), use_text, true)
	if use_text2 != "":
		_draw_scroll(Rect2(s.x * 0.5 - 150, s.y * 0.62 + 92, 300, 70), use_text2, true, "X")
	if bow and bow.equipped:
		var t := "RT: napnout a pustit" if not bow.drawing else ("Pusť RT!" if float(bow.draw) >= 1.0 else "Drž RT…")
		_text(Vector2(s.x - 24, s.y - 40), t, 22, Color(1, 0.93, 0.75, 0.9), HORIZONTAL_ALIGNMENT_RIGHT, 0.0)
		_text(Vector2(s.x - 24, 60), _score_line, 22, Color(1, 0.93, 0.75, 0.95), HORIZONTAL_ALIGNMENT_RIGHT, 0.0)
	if _place_t > 0.0:
		_text(Vector2(c.x, 62), _place, 34, Color(0.97, 0.92, 0.8, clampf(_place_t, 0.0, 1.0)))
	if _toast_t > 0.0:
		_text(Vector2(c.x, s.y * 0.56), _toast, 30, Color(1, 0.9, 0.62, clampf(_toast_t / 0.4, 0.0, 1.0)))
