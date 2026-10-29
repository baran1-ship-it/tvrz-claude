extends CharacterBody3D
## Prozatímní hráč pro procházení terénu (chůze, pohled myší/dotykem). Plné ovládání (dotyk + Xbox, pad.gd)
## se převezme z Havrana v kroku B – zde jen tolik, aby šlo ověřit průchodnost a výhledy.

@export var rychlost := 1.6      # chůze ~1,6 m/s (KCD chůze), Shift běh
@export var beh := 5.0
var cam: Camera3D
var _yaw := 0.0
var _pitch := 0.0

func _ready() -> void:
	cam = $Kamera
	_yaw = rotation.y

func _unhandled_input(e: InputEvent) -> void:
	if e is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_yaw -= e.relative.x * 0.003
		_pitch = clampf(_pitch - e.relative.y * 0.003, -1.4, 1.4)
	elif e is InputEventMouseButton and e.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif e is InputEventKey and e.pressed and e.keycode == KEY_ESCAPE:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _physics_process(dt: float) -> void:
	rotation.y = _yaw
	cam.rotation.x = _pitch
	var v := Vector3.ZERO
	if Input.is_key_pressed(KEY_W): v.z -= 1
	if Input.is_key_pressed(KEY_S): v.z += 1
	if Input.is_key_pressed(KEY_A): v.x -= 1
	if Input.is_key_pressed(KEY_D): v.x += 1
	v = (transform.basis * v).normalized() * (beh if Input.is_key_pressed(KEY_SHIFT) else rychlost)
	velocity.x = v.x; velocity.z = v.z
	velocity.y = 0.0 if is_on_floor() else velocity.y - 9.8 * dt
	move_and_slide()
