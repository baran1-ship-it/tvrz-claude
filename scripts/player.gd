extends CharacterBody3D
## Hrac v prvni osobe: chuze, beh, skok, rozhlizeni a kroky.
## Vstupy nastavuje HUD: move_input (x vpravo, y dopredu), look(), jump().

signal stepped(surface: String, loud: float)

const WALK := 2.3
const RUN := 4.8
const DRAW_SLOW := 0.45      # zpomaleni pri napnutem luku
const JUMP_V := 4.4
const EYE := 1.62
const LIMIT := 128.0         # dal uz neni podrobny teren
const STEP := 0.45           # nejvyssi schod, na ktery hrac vyjde

var move_input := Vector2.ZERO
var yaw := 0.0
var pitch := 0.0
var slow := 1.0              # nastavuje luk
var head: Node3D
var cam: Camera3D
var surface_at: Callable     # func(pos: Vector3) -> String

var _jump := false
var _step := 0.0
var _bob := 0.0
var _land_kick := 0.0
var _was_floor := true
var _gravity := 12.0


func _ready() -> void:
	_gravity = float(ProjectSettings.get_setting("physics/3d/default_gravity", 12.0))
	var col := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.28
	cap.height = 1.76
	col.shape = cap
	col.position.y = 0.88
	add_child(col)
	head = Node3D.new()
	head.name = "Hlava"
	head.position.y = EYE
	add_child(head)
	cam = Camera3D.new()
	cam.name = "Kamera"
	cam.fov = 72.0
	cam.near = 0.04
	cam.far = 2200.0
	head.add_child(cam)
	cam.make_current()
	floor_max_angle = deg_to_rad(52.0)
	floor_snap_length = 0.45
	floor_constant_speed = true
	floor_block_on_wall = true
	max_slides = 6


func place(pos: Vector3, look_at_point: Vector3) -> void:
	global_position = pos
	var d := look_at_point - (pos + Vector3(0, EYE, 0))
	yaw = atan2(-d.x, -d.z)
	pitch = atan2(d.y, Vector2(d.x, d.z).length())
	velocity = Vector3.ZERO
	_apply_rot()


func look(dx: float, dy: float) -> void:
	yaw -= dx
	pitch = clampf(pitch - dy, deg_to_rad(-84.0), deg_to_rad(84.0))
	_apply_rot()


func jump() -> void:
	_jump = true


func forward() -> Vector3:
	return -cam.global_transform.basis.z


func _apply_rot() -> void:
	rotation = Vector3(0.0, yaw, 0.0)
	if head:
		head.rotation = Vector3(pitch, 0.0, 0.0)


func _physics_process(delta: float) -> void:
	_apply_rot()
	var basis_y := Basis(Vector3.UP, yaw)
	var fwd := -basis_y.z
	var right := basis_y.x
	var inp := move_input
	if inp.length() > 1.0:
		inp = inp.normalized()
	var run := inp.length() > 0.92 and inp.y > 0.5 and slow > 0.9
	var speed := (RUN if run else WALK) * slow
	var wish := (right * inp.x + fwd * inp.y) * speed
	var on_floor := is_on_floor()
	var accel := 11.0 if on_floor else 2.5
	velocity.x = lerpf(velocity.x, wish.x, minf(1.0, accel * delta))
	velocity.z = lerpf(velocity.z, wish.z, minf(1.0, accel * delta))
	if on_floor:
		if _jump:
			velocity.y = JUMP_V
			on_floor = false
	else:
		velocity.y -= _gravity * delta
	_jump = false
	var pre_vel := velocity
	move_and_slide()
	# schod nebo prah: zkus se na nej vysunout
	if on_floor and is_on_wall() and Vector2(wish.x, wish.z).length() > 0.3:
		_step_up(Vector3(wish.x, 0, wish.z).normalized() * maxf(0.12, Vector2(pre_vel.x, pre_vel.z).length() * delta), pre_vel)

	# hranice sveta: dal uz je jen vzdaleny teren bez kolizi
	var flat := Vector2(global_position.x, global_position.z)
	if flat.length() > LIMIT:
		flat = flat.normalized() * LIMIT
		global_position.x = flat.x
		global_position.z = flat.y
	if global_position.y < -40.0:
		global_position = Vector3(0, 2, 30)
		velocity = Vector3.ZERO

	# kroky a pohupovani hlavy
	var hv := Vector2(velocity.x, velocity.z).length()
	var floor_now := is_on_floor()
	if floor_now and not _was_floor:
		_land_kick = 0.06
		stepped.emit(_surface(), 1.2)
	_was_floor = floor_now
	if floor_now and hv > 0.4:
		_step += hv * delta
		_bob += hv * delta * 2.2
		var stride := 0.72 if hv < 3.5 else 0.95
		if _step >= stride:
			_step = 0.0
			stepped.emit(_surface(), clampf(hv / RUN, 0.35, 1.0))
	else:
		_bob = lerpf(_bob, roundf(_bob / PI) * PI, minf(1.0, delta * 6.0))
	_land_kick = maxf(0.0, _land_kick - delta * 0.35)
	var amp := clampf(hv / RUN, 0.0, 1.0) * 0.035
	head.position.y = EYE + absf(sin(_bob)) * amp - amp * 0.5 - _land_kick
	head.position.x = cos(_bob) * amp * 0.5


func _step_up(motion: Vector3, pre_vel: Vector3) -> void:
	var xf := global_transform
	if test_move(xf, Vector3.UP * STEP):
		return
	var up := xf.translated(Vector3.UP * STEP)
	if test_move(up, motion):
		return
	var ahead := up.translated(motion)
	var col := KinematicCollision3D.new()
	if not test_move(ahead, Vector3.DOWN * (STEP + 0.05), col):
		return
	if col.get_normal().y < cos(floor_max_angle):
		return
	var rise := STEP - col.get_travel().length()
	if rise < 0.02:
		return
	global_position = ahead.origin + col.get_travel()
	velocity.x = pre_vel.x
	velocity.z = pre_vel.z
	_land_kick = minf(0.05, _land_kick + rise * 0.15)


func _surface() -> String:
	if surface_at.is_valid():
		return surface_at.call(global_position)
	return "stone"
