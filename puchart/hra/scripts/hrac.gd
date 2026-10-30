extends CharacterBody3D
## Hráč pro procházku (tablet + Xbox + PC). Dotyk: levá půlka = páčka chůze (tažením), pravá půlka = rozhled.
## Ovladač: levá páčka chůze, pravá rozhled, LT/RT = běh. PC: WASD + myš, Shift běh.
## Plné ovládání Havrana (pad.gd, menu) se převezme později – tady jen procházka pro prohlídku hradů a krajiny.

@export var rychlost := 1.6      # chůze ~1,6 m/s (KCD), běh 5 m/s
@export var beh := 5.0
var cam: Camera3D
var _yaw := 0.0
var _pitch := 0.0
var _tah_pohyb := -1          # index prstu na levé půlce
var _tah_pohled := -1
var _start := Vector2.ZERO
var _pohyb := Vector2.ZERO    # -1..1 z dotyku
var bezi := false             # přepínač běhu (tlačítko)
var leti := false             # létání (tlačítko Létání / klávesa F): bez gravitace a bez kolize, dopředu = kam se díváš
var vzhuru := 0.0             # létání nahoru/dolů (držená tlačítka, E/Q, LB/RB)
@export var let := 6.0        # rychlost letu m/s, s během 18 m/s
var ui: Array = []            # tlačítka procházky: dotyk na nich nehýbe postavou ani pohledem
var autopilot := Vector3.INF  # test průchodu: jdi rovně k bodu (jen vodorovně, gravitace a kolize platí)

func _ready() -> void:
	cam = $Kamera
	_yaw = rotation.y

func nastav_pohled(yaw: float, pitch := 0.0) -> void:
	_yaw = yaw; _pitch = pitch

func _input(e: InputEvent) -> void:
	if not is_physics_processing():
		return
	var w := get_viewport().get_visible_rect().size.x
	if e is InputEventScreenTouch:
		if e.pressed and ui.any(func(c): return c.is_visible_in_tree() and c.get_global_rect().has_point(e.position)):
			return
		if e.pressed:
			if e.position.x < w * 0.45 and _tah_pohyb < 0:
				_tah_pohyb = e.index; _start = e.position
			elif e.position.x >= w * 0.45 and _tah_pohled < 0:
				_tah_pohled = e.index
		else:
			if e.index == _tah_pohyb: _tah_pohyb = -1; _pohyb = Vector2.ZERO
			if e.index == _tah_pohled: _tah_pohled = -1
	elif e is InputEventScreenDrag:
		if e.index == _tah_pohyb:
			_pohyb = ((e.position - _start) / 110.0).limit_length(1.0)
		elif e.index == _tah_pohled:
			_yaw -= e.relative.x * 0.005
			_pitch = clampf(_pitch - e.relative.y * 0.005, -1.4, 1.4)
	elif e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw -= e.relative.x * 0.003
		_pitch = clampf(_pitch - e.relative.y * 0.003, -1.4, 1.4)
	elif e is InputEventMouseButton and e.pressed and OS.has_feature("pc"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif e is InputEventKey and e.pressed and e.keycode == KEY_ESCAPE:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif e is InputEventKey and e.pressed and not e.echo and e.keycode == KEY_F:
		prepni_let()

func prepni_let() -> void:
	leti = not leti
	collision_layer = 0 if leti else 1; collision_mask = 0 if leti else 1
	velocity = Vector3.ZERO

func _physics_process(dt: float) -> void:
	# ovladač
	var lx := Input.get_joy_axis(0, JOY_AXIS_LEFT_X); var ly := Input.get_joy_axis(0, JOY_AXIS_LEFT_Y)
	var rx := Input.get_joy_axis(0, JOY_AXIS_RIGHT_X); var ry := Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y)
	if absf(rx) > 0.15: _yaw -= rx * 2.4 * dt
	if absf(ry) > 0.15: _pitch = clampf(_pitch - ry * 1.8 * dt, -1.4, 1.4)
	rotation.y = _yaw
	cam.rotation.x = _pitch
	var v := Vector3(_pohyb.x, 0, _pohyb.y)
	if Vector2(lx, ly).length() > 0.15: v = Vector3(lx, 0, ly)
	if Input.is_key_pressed(KEY_W): v.z -= 1
	if Input.is_key_pressed(KEY_S): v.z += 1
	if Input.is_key_pressed(KEY_A): v.x -= 1
	if Input.is_key_pressed(KEY_D): v.x += 1
	var rychle := bezi or Input.is_key_pressed(KEY_SHIFT) or Input.get_joy_axis(0, JOY_AXIS_TRIGGER_RIGHT) > 0.5
	if leti:
		var nah := vzhuru
		if Input.is_key_pressed(KEY_E) or Input.is_key_pressed(KEY_SPACE) or Input.is_joy_button_pressed(0, JOY_BUTTON_RIGHT_SHOULDER): nah += 1.0
		if Input.is_key_pressed(KEY_Q) or Input.is_key_pressed(KEY_C) or Input.is_joy_button_pressed(0, JOY_BUTTON_LEFT_SHOULDER): nah -= 1.0
		var smer := cam.global_transform.basis * v.limit_length(1.0) + Vector3.UP * clampf(nah, -1.0, 1.0)
		velocity = smer * (let * (3.0 if rychle else 1.0))
		move_and_slide()
		return
	if autopilot != Vector3.INF:
		var k := Vector3(autopilot.x - position.x, 0, autopilot.z - position.z)
		v = k.normalized() * rychlost if k.length() > 0.05 else Vector3.ZERO
	else:
		v = (transform.basis * v.limit_length(1.0)) * (beh if rychle else rychlost)
	velocity.x = v.x; velocity.z = v.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - 9.8 * dt
	floor_snap_length = 0.6
	floor_max_angle = deg_to_rad(50)
	move_and_slide()
