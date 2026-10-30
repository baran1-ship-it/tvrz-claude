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
	v = (transform.basis * v.limit_length(1.0)) * (beh if rychle else rychlost)
	velocity.x = v.x; velocity.z = v.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - 9.8 * dt
	floor_snap_length = 0.6
	floor_max_angle = deg_to_rad(50)
	move_and_slide()
