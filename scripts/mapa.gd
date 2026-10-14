extends CanvasLayer
## Mapa kraje (kriz nahoru nebo ikona mapy): pergamenova mapa z tools/gen_mapa.py (nazvy mist jsou v obraze),
## poloha a smer hrace,
## erby mist pro rychle cestovani (Tvrz, Lhota). Vyber erbu (dotyk, nebo kriz/packa + A) se zepta,
## zda cestovat; cesta ubehne herni cas podle vzdalenosti. B / kriz nahoru / Start zavre.

const GOLD := Color(0.89, 0.73, 0.41)
const INK := Color(0.2, 0.12, 0.06)
const X0 := -240.0
const X1 := 890.0
const Z0 := -240.0
const Z1 := 1340.0
const MISTA := [
	{"id": "tvrz", "nazev": "Tvrz Havran", "erb": "venku", "p": Vector2(0.0, 0.0),
		"cil": Vector3(2.5, 0.0, 40.0), "pohled": Vector3(0.0, 4.5, 15.0)},
	{"id": "ves", "nazev": "Lhota", "erb": "jidlo", "p": Vector2(470.0, 830.0),
		"cil": Vector3(413.0, 0.0, 781.0), "pohled": Vector3(470.0, 3.0, 830.0)},
	{"id": "hostinec", "nazev": "Zájezdní hostinec", "erb": "piti", "p": Vector2(-71.0, 881.0),
		"cil": Vector3(-53.2, 0.0, 878.1), "pohled": Vector3(-71.0, 3.0, 881.0)},
]

var main: Node
var open := false
var sel := 0
var asking := false            # dotaz "Rychle cestovat?"
var ano := true                # vybrana odpoved v dotazu
var _c: Control
var _tex: Texture2D
var _erby := {}
var _fb: Font
var _fm: Font
var _rects: Array = []         # [Rect2, akce, arg]
var _opened_ms := 0
var _stick := false


func _ready() -> void:
	layer = 19
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	_tex = load("res://obrazky/mapa.png") if ResourceLoader.exists("res://obrazky/mapa.png") else null
	_fb = load("res://fonts/GrenzeGotisch-Bold.ttf")
	_fm = load("res://fonts/GrenzeGotisch-Medium.ttf")
	for m: Dictionary in MISTA:
		_erby[m["erb"]] = load("res://obrazky/erby/%s.png" % m["erb"])
	_c = Control.new()
	_c.set_anchors_preset(Control.PRESET_FULL_RECT)
	_c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_c.draw.connect(_draw_all)
	add_child(_c)


func show_map() -> void:
	if open or _tex == null:
		return
	open = true
	asking = false
	visible = true
	_opened_ms = Time.get_ticks_msec()
	# vybrane je misto, kde hrac neni (kam se nejspis chce dostat)
	sel = 1 if _here() == 0 else 0
	main.hud.visible = false
	get_tree().paused = true
	main.life.sfx("menu", -6.0)
	_c.queue_redraw()


func close() -> void:
	if not open:
		return
	open = false
	visible = false
	main.hud.visible = true
	get_tree().paused = false


func _here() -> int:
	var pp: Vector3 = main.player.global_position
	var best := 0
	var bd := 1e9
	for i in MISTA.size():
		var d := Vector2(pp.x, pp.z).distance_to(MISTA[i]["p"])
		if d < bd:
			bd = d
			best = i
	return best


# ------------------------------------------------------------------ kresleni

func _map_rect() -> Rect2:
	var s := _c.get_viewport_rect().size
	var ts := _tex.get_size()
	var k := minf((s.x - 40.0) / ts.x, (s.y - 40.0) / ts.y)
	var sz := ts * k
	return Rect2((s - sz) * 0.5, sz)


func _to_screen(r: Rect2, x: float, z: float) -> Vector2:
	return r.position + Vector2((x - X0) / (X1 - X0) * r.size.x, (z - Z0) / (Z1 - Z0) * r.size.y)


func _draw_all() -> void:
	_rects.clear()
	var s := _c.get_viewport_rect().size
	_c.draw_rect(Rect2(Vector2.ZERO, s), Color(0.04, 0.03, 0.02, 0.92))
	var r := _map_rect()
	_c.draw_texture_rect(_tex, r, false)
	var u := clampf(r.size.y / 900.0, 0.6, 1.6)
	# mista: erb a nazev
	for i in MISTA.size():
		var m: Dictionary = MISTA[i]
		var c := _to_screen(r, m["p"].x, m["p"].y)
		var es := 58.0 * u * (1.18 if i == sel else 1.0)
		var er := Rect2(c - Vector2(es * 0.5, es * 1.1), Vector2(es, es))
		if i == sel:
			_c.draw_circle(er.get_center(), es * 0.7, Color(1.0, 0.85, 0.45, 0.45))
		_c.draw_texture_rect(_erby[m["erb"]], er, false)
		_rects.append([er.grow(12), "misto", i])
	# hrac: sipka ve smeru pohledu
	var pp: Vector3 = main.player.global_position
	var pc := _to_screen(r, pp.x, pp.z)
	var yaw: float = main.player.yaw
	var fwd := Vector2(-sin(yaw), -cos(yaw))
	var side := Vector2(-fwd.y, fwd.x)
	var a := 16.0 * u
	var pts := PackedVector2Array([pc + fwd * a, pc - fwd * a * 0.6 + side * a * 0.65, pc - fwd * a * 0.25, pc - fwd * a * 0.6 - side * a * 0.65])
	_c.draw_colored_polygon(pts, Color(0.7, 0.08, 0.05))
	_c.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0.15, 0.05, 0.02), 2.0, true)
	# napoveda dole
	var hint := "Klepni na erb nebo vyber křížem a potvrď A  ·  B zavřít"
	_text(Vector2(s.x * 0.5, s.y - 14), hint, int(20 * u), Color(0.95, 0.88, 0.7), Color(0, 0, 0, 0.6))
	# zavrit (dotyk)
	var cr := Rect2(Vector2(s.x - 86, 18), Vector2(68, 60))
	_c.draw_rect(cr, Color(0, 0, 0, 0.45))
	_c.draw_line(cr.position + Vector2(20, 14), cr.end - Vector2(20, 14), Color(1, 1, 1, 0.85), 4.0)
	_c.draw_line(Vector2(cr.end.x - 20, cr.position.y + 14), Vector2(cr.position.x + 20, cr.end.y - 14), Color(1, 1, 1, 0.85), 4.0)
	_rects.append([cr, "zavrit", 0])
	if asking:
		_draw_ask(s, u)


func _draw_ask(s: Vector2, u: float) -> void:
	_rects.clear()
	var m: Dictionary = MISTA[sel]
	var w := 620.0 * u
	var h := 250.0 * u
	var box := Rect2((s - Vector2(w, h)) * 0.5, Vector2(w, h))
	_c.draw_rect(box, Color(0.93, 0.85, 0.66))
	_c.draw_rect(box, Color(0.45, 0.3, 0.14), false, 4.0)
	_text(box.position + Vector2(w * 0.5, 62 * u), "Rychle cestovat", int(34 * u), INK, Color(0, 0, 0, 0))
	var km := _dist_km()
	_text(box.position + Vector2(w * 0.5, 108 * u), "do: %s  (asi %d minut chůze)" % [m["nazev"], int(round(km / 4.5 * 60.0))], int(24 * u), INK, Color(0, 0, 0, 0))
	for k in 2:
		var br := Rect2(box.position + Vector2(w * (0.12 + 0.44 * k), h - 92 * u), Vector2(w * 0.32, 62 * u))
		var on := (k == 0) == ano
		_c.draw_rect(br, Color(0.45, 0.12, 0.08) if on else Color(0.3, 0.22, 0.14))
		_c.draw_rect(br, GOLD if on else Color(0.5, 0.4, 0.25), false, 3.0)
		_text(br.get_center() + Vector2(0, 10 * u), "Ano" if k == 0 else "Ne", int(28 * u), GOLD if on else Color(0.85, 0.78, 0.62), Color(0, 0, 0, 0))
		_rects.append([br, "odpoved", k == 0])


func _text(p: Vector2, t: String, size: int, col: Color, bg: Color) -> void:
	var w := _fm.get_string_size(t, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	if bg.a > 0.0:
		_c.draw_rect(Rect2(p - Vector2(w * 0.5 + 8, size * 0.95), Vector2(w + 16, size * 1.25)), bg)
	_c.draw_string(_fm, p - Vector2(w * 0.5, 0), t, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


# ------------------------------------------------------------------ ovladani

func _input(event: InputEvent) -> void:
	if not open:
		return
	if event is InputEventJoypadButton and event.pressed:
		get_viewport().set_input_as_handled()
		if Time.get_ticks_msec() - _opened_ms < 250:
			return
		var b := (event as InputEventJoypadButton).button_index
		if asking:
			match b:
				JOY_BUTTON_A:
					_answer(ano)
				JOY_BUTTON_B:
					_answer(false)
				JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT:
					ano = not ano
					main.life.sfx("click", -10.0, 0.8)
			_c.queue_redraw()
			return
		match b:
			JOY_BUTTON_B, JOY_BUTTON_START, JOY_BUTTON_DPAD_UP:
				close()
			JOY_BUTTON_A:
				_ask()
			JOY_BUTTON_DPAD_LEFT, JOY_BUTTON_DPAD_RIGHT, JOY_BUTTON_DPAD_DOWN, JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER:
				sel = (sel + 1) % MISTA.size()
				main.life.sfx("click", -10.0, 0.8)
		_c.queue_redraw()
	elif event is InputEventJoypadMotion:
		var v := Input.get_joy_axis(0, JOY_AXIS_LEFT_X)
		if absf(v) > 0.6 and not _stick:
			_stick = true
			if asking:
				ano = not ano
			else:
				sel = (sel + 1) % MISTA.size()
			_c.queue_redraw()
		elif absf(v) < 0.3:
			_stick = false
	elif (event is InputEventScreenTouch and event.pressed) or (event is InputEventMouseButton and event.pressed):
		get_viewport().set_input_as_handled()
		var pos: Vector2 = event.position
		for rr: Array in _rects:
			if (rr[0] as Rect2).has_point(pos):
				match String(rr[1]):
					"zavrit":
						close()
					"misto":
						sel = int(rr[2])
						_ask()
					"odpoved":
						_answer(bool(rr[2]))
				break
		_c.queue_redraw()
	elif event is InputEventKey and event.pressed and (event as InputEventKey).keycode in [KEY_ESCAPE, KEY_M]:
		close()


func _dist_km() -> float:
	var pp: Vector3 = main.player.global_position
	var m: Dictionary = MISTA[sel]
	# po cestach je to zhruba o polovinu dal nez vzdusnou carou
	return Vector2(pp.x, pp.z).distance_to(m["p"]) * 1.35 / 1000.0


func _ask() -> void:
	if Vector2(main.player.global_position.x, main.player.global_position.z).distance_to(MISTA[sel]["p"]) < 60.0:
		main.hud.toast("Tady už jsi.", 1.6)
		close()
		return
	asking = true
	ano = true
	main.life.sfx("click", -8.0, 1.0)


func _answer(yes: bool) -> void:
	asking = false
	if not yes:
		_c.queue_redraw()
		return
	var m: Dictionary = MISTA[sel]
	var hours := _dist_km() / 4.5
	close()
	main.fast_travel(m["cil"], m["pohled"], hours, String(m["nazev"]))
