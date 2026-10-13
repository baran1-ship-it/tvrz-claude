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
		if main.menu_hrace and main.menu_hrace.open:
			return
		if b == JOY_BUTTON_START:
			main._pause(false)
			get_viewport().set_input_as_handled()
		return
	# pokladani predmetu: A polozit, B zrusit (otaceni spoustemi v _process)
	if main.predmety.placing != "":
		if b == JOY_BUTTON_A:
			main.predmety.confirm_place()
		elif b == JOY_BUTTON_B:
			main.predmety.cancel_and_back()
		return
	match b:
		JOY_BUTTON_DPAD_DOWN:
			main.open_player_menu()
		JOY_BUTTON_DPAD_RIGHT:
			main.toggle_build()
		JOY_BUTTON_START, JOY_BUTTON_BACK:
			main._pause(true)
		JOY_BUTTON_B:
			if main.build_mode:
				main.toggle_build()
				return
			if main.player.can_fly and not main.player.flying:
				main.player.set_flying(true)
		JOY_BUTTON_A:
			# A: pouzit (dvere, navijak), kdyz je neco na dosah, jinak skok
			if not main._use.is_empty() or (main.predmety.held_id != "" and not main.build_mode):
				main._on_use()
			else:
				main.player.jump()
		JOY_BUTTON_X:
			if main.build_mode or main.hud.use_text2 != "":
				main._on_use2()
			else:
				main._on_use()
		JOY_BUTTON_Y:
			main.day.set_time(main.day.next_key(), 2.0)
			main.hud.toast("Denní doba: %s" % main.day.NAMES[main.day.current], 1.5)
			main._save_cfg()


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
	if p.flying:
		p.fly_up = Input.is_joy_button_pressed(0, JOY_BUTTON_A)
		p.fly_down = Input.is_joy_button_pressed(0, JOY_BUTTON_B)
	var lk := _stick(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
	if lk != Vector2.ZERO:
		var k := LOOK_SPEED * float(main.hud.sens) * delta
		if main.bow and main.bow.drawing:
			k *= 0.55
		# mirne zrychleni u kraje, jemne miereni u stredu
		var curve := lk * lk.length()
		p.look(curve.x * k, curve.y * k * 0.8)
	var rt := _axis(JOY_AXIS_TRIGGER_RIGHT)
	if main.predmety.placing != "":
		main.predmety.rotate_place((_axis(JOY_AXIS_TRIGGER_LEFT) - rt) * 2.2 * delta)
		return
	if main.bow and main.bow.equipped:
		if rt > 0.5 and not _rt_down:
			_rt_down = true
			main.bow.begin_draw()
		elif rt < 0.3 and _rt_down:
			_rt_down = false
			main.bow.release()
	else:
		_rt_down = false
