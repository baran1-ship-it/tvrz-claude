extends CharacterBody3D
## Hrac v prvni osobe: chuze, beh, skok, rozhlizeni a kroky.
## Vstupy nastavuje HUD: move_input (x vpravo, y dopredu), look(), jump().

signal stepped(surface: String, loud: float)

const WALK := 2.3
const RUN := 4.8
const DRAW_SLOW := 0.45      # zpomaleni pri napnutem luku
const JUMP_V := 4.4
const EYE := 1.62
const AREA := Rect2(-240.0, -240.0, 1130.0, 1580.0)   # kam se da dojit (x od -240 do 890, z od -240 do 1340)
const FLY := 7.0             # rychlost letu (piskoviste)
const FLY_FAST := 16.0
const STEP := 0.45           # nejvyssi schod, na ktery hrac vyjde

var move_input := Vector2.ZERO
var move_curve := 1.6          # nastaveni "Pohyb packou": krivka vychyleni -> rychlost
var yaw := 0.0
var pitch := 0.0
var slow := 1.0              # nastavuje luk
var head: Node3D
var cam: Camera3D
var surface_at: Callable     # func(pos: Vector3) -> String
var can_fly := false         # piskoviste: dvojity skok prepina let
var flying := false
var beh := false             # rezim behu (prepinac na obrazovce / leva packa ovladace); jinak jen chuze
var fly_up := false          # drzene tlacitko skoku
var fly_down := false        # drzene tlacitko dolu
signal fly_changed(on: bool)
var _last_jump := -10.0
var _eye_y := EYE

var _jump := false
var _step := 0.0
var _bob := 0.0
var _land_kick := 0.0
var _air_t := 0.0
var _was_floor := true
var _gravity := 12.0
# sezeni a lezeni: hrac je pripoutan k mistu, pohyb nebo skok ho zvedne
var seated := false
var _seat_p := Vector3.ZERO
var _stand_p := Vector3.ZERO
var _seat_eye := 1.2
signal stood_up


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
	# kamera se kresli kazdy snimek z interpolovane polohy tela (plynule i na 120 Hz displeji)
	cam.top_level = true
	cam.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	add_child(cam)
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
	reset_physics_interpolation()
	_update_cam()


func look(dx: float, dy: float) -> void:
	yaw -= dx
	pitch = clampf(pitch - dy, deg_to_rad(-84.0), deg_to_rad(84.0))
	_apply_rot()


func jump() -> void:
	var now := Time.get_ticks_msec() / 1000.0
	if can_fly and now - _last_jump < 0.32:
		set_flying(not flying)
		_last_jump = -10.0
		return
	_last_jump = now
	_jump = true


func sit(p: Vector3, eye_h: float, stand_p: Vector3, face_yaw: float, look_pitch := 0.0) -> void:
	if flying:
		set_flying(false)
	seated = true
	_seat_p = p
	_stand_p = stand_p
	_seat_eye = eye_h
	global_position = p
	velocity = Vector3.ZERO
	yaw = face_yaw
	pitch = look_pitch
	_apply_rot()
	reset_physics_interpolation()


func stand_up() -> void:
	if not seated:
		return
	seated = false
	global_position = _stand_p
	velocity = Vector3.ZERO
	pitch = 0.0
	_apply_rot()
	reset_physics_interpolation()
	stood_up.emit()


func set_flying(on: bool) -> void:
	if flying == on:
		return
	flying = on
	velocity.y = 0.0
	fly_changed.emit(on)


func forward() -> Vector3:
	return -cam.global_transform.basis.z


func _apply_rot() -> void:
	rotation = Vector3(0.0, yaw, 0.0)
	if head:
		head.rotation = Vector3(pitch, 0.0, 0.0)


func _process(_delta: float) -> void:
	_update_cam()


func _update_cam() -> void:
	if cam == null:
		return
	# poloha z interpolace fyziky, otoceni primo ze vstupu (bez zpozdeni)
	var o := get_global_transform_interpolated().origin if is_inside_tree() else global_position
	var bas := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, pitch)
	cam.global_transform = Transform3D(bas, o + Vector3(0, _eye_y, 0) + Basis(Vector3.UP, yaw) * Vector3(head.position.x, 0, 0))


func _physics_process(delta: float) -> void:
	_apply_rot()
	if seated:
		_eye_y = lerpf(_eye_y, _seat_eye, minf(1.0, delta * 6.0))
		if move_input.length() > 0.5 or _jump:
			_jump = false
			stand_up()
		return
	var basis_y := Basis(Vector3.UP, yaw)
	var fwd := -basis_y.z
	var right := basis_y.x
	var inp := move_input
	if inp.length() > 1.0:
		inp = inp.normalized()
	var ml := inp.length()
	if ml < 0.15:
		beh = false               # zastaveni = konec behu (ovladac i dotyk)
	var run := beh and ml > 0.5 and slow > 0.9
	if ml > 0.0:
		inp *= pow(ml, move_curve) / ml
	if run:
		inp = inp.normalized()
	if flying:
		_fly(delta, inp, run)
		return
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
	# (obdelnik pasma 5 m z blender/kraj.py ACT: okoli tvrze, cesty, skalni mesto a vesnice)
	global_position.x = clampf(global_position.x, AREA.position.x, AREA.end.x)
	global_position.z = clampf(global_position.z, AREA.position.y, AREA.end.y)
	if global_position.y < -90.0:
		global_position = Vector3(0, 2, 30)
		velocity = Vector3.ZERO

	# kroky a pohupovani hlavy
	var hv := Vector2(velocity.x, velocity.z).length()
	var floor_now := is_on_floor()
	# kroky (chuze, beh) a dopad po skoku nebo letu; kratke odlepeni na schodech se nepocita
	if floor_now and not _was_floor:
		_land_kick = 0.06
		if _air_t > 0.3:
			stepped.emit(_surface(), 1.2)
	_air_t = 0.0 if floor_now else _air_t + delta
	_was_floor = floor_now
	if floor_now and hv > 0.4:
		_step += hv * delta
		_bob += hv * delta * 2.2
		var stride := 1.15 if hv < 3.5 else 1.5   # ~2 kroky za sekundu pri chuzi
		if _step >= stride:
			_step = 0.0
			pass                    # kroky vypnute (Misa 19. 10.: zvuky pozdeji); dopad po skoku/letu zustava
	else:
		_bob = lerpf(_bob, roundf(_bob / PI) * PI, minf(1.0, delta * 6.0))
	_land_kick = maxf(0.0, _land_kick - delta * 0.35)
	var amp := clampf(hv / RUN, 0.0, 1.0) * 0.035
	head.position.y = EYE + absf(sin(_bob)) * amp - amp * 0.5 - _land_kick
	head.position.x = cos(_bob) * amp * 0.5
	_eye_y = head.position.y


func _fly(delta: float, inp: Vector2, fast: bool) -> void:
	# let: smer pohledu vcetne naklonu, nahoru/dolu tlacitky
	var look_basis := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, pitch)
	var dir := look_basis * Vector3(inp.x, 0, -inp.y)
	var vert := (1.0 if fly_up else 0.0) - (1.0 if fly_down else 0.0)
	var wish := dir * (FLY_FAST if fast else FLY) + Vector3.UP * vert * FLY
	velocity = velocity.lerp(wish, minf(1.0, 6.0 * delta))
	move_and_slide()
	if fly_down and is_on_floor():
		set_flying(false)      # pristani
	if global_position.y > 120.0:
		global_position.y = 120.0
	head.position = Vector3(0, EYE, 0)
	_eye_y = EYE
	_jump = false


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
