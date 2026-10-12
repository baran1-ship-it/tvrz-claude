extends CanvasLayer
## Dotykove ovladani a ukazatele. Vlevo plovouci packa pro chuzi, vpravo tazenim rozhlizeni,
## tlacitka kreslena primo (bez Control uzlu), aby slo ovladat vic prsty naraz.

signal use_pressed
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
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	_loading.add_child(v)
	var t := _label("Odkaz Havrana", 84, Color(0.93, 0.8, 0.52))
	t.add_theme_font_override("font", load("res://fonts/GrenzeGotisch-Bold.ttf"))
	v.add_child(t)
	var t2 := _label("Načítám tvrz…", 30, Color(0.7, 0.62, 0.48))
	t2.add_theme_font_override("font", load("res://fonts/GrenzeGotisch-Medium.ttf"))
	v.add_child(t2)
	v.position = Vector2(-260, -70)
	v.custom_minimum_size = Vector2(520, 140)


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
	# pouziti
	if use_text != "":
		var ur := _btn_use()
		var sbx := StyleBoxFlat.new()
		sbx.bg_color = Color(0.1, 0.08, 0.06, 0.7)
		sbx.border_color = Color(0.9, 0.78, 0.55, 0.85)
		sbx.set_border_width_all(2)
		sbx.set_corner_radius_all(12)
		_pad.draw_style_box(sbx, ur)
		_text(ur.position + Vector2(ur.size.x * 0.5, ur.size.y * 0.5 + 9), use_text, 26, Color(1, 0.95, 0.85))
	# misto a zpravy
	if _place_t > 0.0:
		var a := clampf(_place_t, 0.0, 1.0)
		_text(Vector2(c.x, 62), _place, 34, Color(0.97, 0.92, 0.8, a))
	if _toast_t > 0.0:
		var a2 := clampf(_toast_t / 0.4, 0.0, 1.0)
		_text(Vector2(c.x, s.y * 0.68), _toast, 30, Color(1, 0.9, 0.62, a2))


func _draw_gamepad_hints(s: Vector2, c: Vector2) -> void:
	if use_text != "":
		var ur := Rect2(s.x * 0.5 - 170, s.y * 0.62, 340, 58)
		var sbx := StyleBoxFlat.new()
		sbx.bg_color = Color(0.1, 0.08, 0.06, 0.7)
		sbx.border_color = Color(0.9, 0.78, 0.55, 0.85)
		sbx.set_border_width_all(2)
		sbx.set_corner_radius_all(12)
		_pad.draw_style_box(sbx, ur)
		_pad.draw_circle(ur.position + Vector2(34, 29), 17, Color(0.25, 0.45, 0.85))
		_text(ur.position + Vector2(34, 37), "X", 22, Color(1, 1, 1))
		_text(ur.position + Vector2(ur.size.x * 0.5 + 20, 38), use_text, 24, Color(1, 0.95, 0.85))
	if bow and bow.equipped:
		var t := "RT: napnout a pustit" if not bow.drawing else ("Pusť RT!" if float(bow.draw) >= 1.0 else "Drž RT…")
		_text(Vector2(s.x - 24, s.y - 40), t, 22, Color(1, 0.93, 0.75, 0.9), HORIZONTAL_ALIGNMENT_RIGHT, 0.0)
		_text(Vector2(s.x - 24, 60), _score_line, 22, Color(1, 0.93, 0.75, 0.95), HORIZONTAL_ALIGNMENT_RIGHT, 0.0)
	if _place_t > 0.0:
		_text(Vector2(c.x, 62), _place, 34, Color(0.97, 0.92, 0.8, clampf(_place_t, 0.0, 1.0)))
	if _toast_t > 0.0:
		_text(Vector2(c.x, s.y * 0.56), _toast, 30, Color(1, 0.9, 0.62, clampf(_toast_t / 0.4, 0.0, 1.0)))
