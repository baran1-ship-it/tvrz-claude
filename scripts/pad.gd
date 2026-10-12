extends Node
## Herni ovladac (Xbox a podobne): leva packa chuze, prava rozhlizeni, A skok, X pouzit,
## pravy trigger napnout luk, Start menu, B zpet z menu.

const DEAD := 0.16
const LOOK_SPEED := 2.7       # rad/s pri plne vychylce

var main: Node
var active := false           # posledni vstup prisel z ovladace
var _rt_down := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func _axis(a: JoyAxis) -> float:
	return Input.get_joy_axis(0, a)


func _stick(ax: JoyAxis, ay: JoyAxis) -> Vector2:
	var v := Vector2(_axis(ax), _axis(ay))
	var m := v.length()
	if m < DEAD:
		return Vector2.ZERO
	return v / m * minf(1.0, (m - DEAD) / (1.0 - DEAD))


func _input(event: InputEvent) -> void:
	if not main.ready_done:
		return
	if event is InputEventJoypadButton or (event is InputEventJoypadMotion and absf((event as InputEventJoypadMotion).axis_value) > 0.4):
		_set_active(true)
	elif event is InputEventScreenTouch:
		_set_active(false)
	if not (event is InputEventJoypadButton) or not event.pressed:
		return
	var b := (event as InputEventJoypadButton).button_index
	if get_tree().paused:
		if b == JOY_BUTTON_START or b == JOY_BUTTON_B:
			main._on_menu("resume")
			get_viewport().set_input_as_handled()
		return
	match b:
		JOY_BUTTON_START, JOY_BUTTON_BACK:
			main._on_menu("open")
			main.hud.focus_menu()
		JOY_BUTTON_A:
			main.player.jump()
		JOY_BUTTON_X:
			main._on_use()
		JOY_BUTTON_Y:
			main.day.set_time(main.day.next_key(), 2.0)
			main.hud.toast("Denní doba: %s" % main.day.NAMES[main.day.current], 1.5)
			main._save()


func _set_active(on: bool) -> void:
	if active == on:
		return
	active = on
	main.hud.gamepad = on
	if not on:
		main.player.move_input = Vector2.ZERO


func _process(delta: float) -> void:
	if not active or not main.ready_done or get_tree().paused:
		return
	var p: CharacterBody3D = main.player
	var mv := _stick(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y)
	p.move_input = Vector2(mv.x, -mv.y)
	var lk := _stick(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
	if lk != Vector2.ZERO:
		var k := LOOK_SPEED * float(main.hud.sens) * delta
		if main.bow.drawing:
			k *= 0.55
		# mirne zrychleni u kraje, jemne miereni u stredu
		var curve := lk * lk.length()
		p.look(curve.x * k, curve.y * k * 0.8)
	var rt := _axis(JOY_AXIS_TRIGGER_RIGHT)
	if main.bow.equipped:
		if rt > 0.5 and not _rt_down:
			_rt_down = true
			main.bow.begin_draw()
		elif rt < 0.3 and _rt_down:
			_rt_down = false
			main.bow.release()
	else:
		_rt_down = false
