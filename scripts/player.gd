extends CharacterBody3D
const Pravidla := preload("res://scripts/pravidla.gd")
## Hrac v prvni osobe: chuze, beh, skok, rozhlizeni a kroky.
## Vstupy nastavuje HUD: move_input (x vpravo, y dopredu), look(), jump().

signal stepped(surface: String, loud: float)

const WALK := 2.3
const RUN := 4.8
const DRAW_SLOW := 0.45      # zpomaleni pri napnutem luku
const JUMP_V := 4.4
const EYE := 1.62
# kam se da dojit (pravidla/svet/svet.json hranice_pruchod)
static var AREA := Rect2(Pravidla.cti("svet", "hranice_pruchod")["x0"], Pravidla.cti("svet", "hranice_pruchod")["z0"],
		Pravidla.cti("svet", "hranice_pruchod")["x1"] - Pravidla.cti("svet", "hranice_pruchod")["x0"],
		Pravidla.cti("svet", "hranice_pruchod")["z1"] - Pravidla.cti("svet", "hranice_pruchod")["z0"])
const FLY := 7.0             # rychlost letu (piskoviste)
const FLY_FAST := 16.0
static var SCHODY: Array = Pravidla.cti("hrac", "schod_m")     # zvednuti pri prekroceni schodu (hrac.json), prvni = nejvyssi
static var STEP := float(SCHODY[0])

var move_input := Vector2.ZERO
var move_curve := 1.6          # nastaveni "Pohyb packou": krivka vychyleni -> rychlost
var yaw := 0.0
var pitch := 0.0
var slow := 1.0              # nastavuje luk
var head: Node3D
var cam: Camera3D
var surface_at: Callable     # func(pos: Vector3) -> String
var can_fly := false         # piskoviste: dvojity skok prepina let
var buh := false             # piskoviste (Misa 28. 10.): zivoty a vydrz stale plne, pady bez skody
var flying := false
var beh := false             # rezim behu (prepinac na obrazovce / leva packa ovladace); jinak jen chuze
# zivoty a vydrz (pravidla/svet/hrac.json, Misa 28. 10. podle KCD2; ukazatel dole - hud.gd _draw_stav)
static var ZIVOTY_MAX := float(Pravidla.cti("hrac", "zivoty_max"))
static var VYDRZ_MAX := float(Pravidla.cti("hrac", "vydrz_max"))
static var BEH_ZA_S := float(Pravidla.cti("hrac", "beh_za_s"))
static var OBNOVA_ZA_S := float(Pravidla.cti("hrac", "obnova_za_s"))
static var OBNOVA_PO_S := float(Pravidla.cti("hrac", "obnova_po_s"))
static var OBNOVA_POHYB := float(Pravidla.cti("hrac", "obnova_pohyb_podil"))   # pri chuzi se vydrz obnovuje pomaleji (KCD2)
static var SKOK_VYDRZ := float(Pravidla.cti("hrac", "skok_vydrz"))
static var PAD: Dictionary = Pravidla.cti("hrac", "pad")                       # bez_skody / zraneni_od / smrt_od (KCD2)
var _air_y0 := 0.0                       # nejvyssi bod ve vzduchu (vyska padu)
static var BEH_ZNOVU_OD := float(Pravidla.cti("hrac", "beh_znovu_od"))
var zivoty := ZIVOTY_MAX
var vydrz := VYDRZ_MAX
var zivoty_max := ZIVOTY_MAX           # pro ukazatel (hud cte vlastnosti, ne staticke)
var vydrz_max := VYDRZ_MAX
var _beh_m := 0.0                 # ubehnuto od posledni udalosti beh_100m (dovednosti: Dech)
var _bez_behu := 0.0
var _vycerpan := false
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
# lezeni po zebriku (FUNKCE 1, Misa: "zebriky v lomu, v domech, na pudy"): hrac na ose zebriku, packa nahoru/dolu,
# nahore vystoupi na sestup (podlaha leseni / pudy), dole na nastup; skok = pustit se
const LEZENI := 1.1          # m/s po zebriku
var climbing := false
var _zb: Dictionary = {}
var _zb_t := 0.0
var _col: CollisionShape3D
signal climb_changed(on: bool)
# jizda na koni (scripts/kun.gd): kun drzi hrace v sedle, cte move_input / beh / yaw; vlastni kolize vypnuta
var na_koni: Node = null:
	set(v):
		na_koni = v
		if _col:
			_col.disabled = v != null
		velocity = Vector3.ZERO


func _ready() -> void:
	_gravity = float(ProjectSettings.get_setting("physics/3d/default_gravity", 12.0))
	var col := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.28
	cap.height = 1.76
	col.shape = cap
	col.position.y = 0.88
	add_child(col)
	_col = col
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
	if na_koni != null:
		# na koni hlava jezdce dozadu jen do jizda.json kun.rozhled_st od smeru kone (Misa 0.991: otocim se dozadu
		# a vidim svoje telo bez hlavy) - KCD2: jezdec se rozhlizi, kun pak zataci za pohledem
		var kz := float((na_koni as Node3D).rotation.y)
		var mez := deg_to_rad(float(Pravidla.cti("jizda", "kun", "rozhled_st")))
		yaw = kz + clampf(wrapf(yaw - kz, -PI, PI), -mez, mez)
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


## Chytit se zebriku: zb {pata, vrchol, nastup, sestup} ve svete; nahore = zacit od vrcholu (slezani).
func climb(zb: Dictionary, nahore: bool) -> void:
	_zb = zb
	# shora kousek pod vrchol: na 1,0 by _lez hned v prvnim kroku vystoupil zpet na sestup (Misa 0.82 "kliknu a hodi
	# me to vedle zebriku")
	_zb_t = 0.96 if nahore else 0.0
	climbing = true
	velocity = Vector3.ZERO
	_col.disabled = true
	var d := (zb["vrchol"] as Vector3) - (zb["pata"] as Vector3)
	yaw = atan2(-d.x, -d.z) if Vector2(d.x, d.z).length() > 0.05 else yaw
	_zb_pos()
	climb_changed.emit(true)


func _zb_pos() -> void:
	var a: Vector3 = _zb["pata"]
	var b: Vector3 = _zb["vrchol"]
	# hrac pred zebrikem (strana nastupu), oci nad pricli
	var pred: Vector3 = (_zb["nastup"] as Vector3) - a
	pred.y = 0.0
	pred = pred.normalized() * 0.32 if pred.length() > 0.01 else Vector3.ZERO
	global_position = a.lerp(b, _zb_t) + pred - Vector3(0, 0.15, 0)


func _end_climb(kam: Vector3) -> void:
	climbing = false
	_col.disabled = false
	if kam != Vector3.INF:
		postav_na_volne(kam)
	velocity = Vector3.ZERO
	climb_changed.emit(false)


func _lez(delta: float) -> void:
	var a: Vector3 = _zb["pata"]
	var b: Vector3 = _zb["vrchol"]
	var dl := maxf(a.distance_to(b), 0.5)
	if _jump:
		_jump = false
		_end_climb(Vector3.INF)          # pustit se
		return
	# Misa 0.88 „zebrik na leseni me chytil a nemohl jsem odejit“: packa do strany = sestoupit/seskocit vedle
	# (dole na nastup, nahore na sestup, uprostred pustit se)
	if absf(move_input.x) > 0.6 and absf(move_input.x) > absf(move_input.y):
		_end_climb(_zb["nastup"] if _zb_t < 0.25 else (_zb["sestup"] if _zb_t > 0.75 else Vector3.INF))
		return
	_zb_t += move_input.y * LEZENI / dl * delta
	if _zb_t >= 1.0 and move_input.y > 0.1:
		_end_climb(_zb["sestup"])
		return
	if _zb_t <= 0.0 and move_input.y < -0.1:
		_end_climb(_zb["nastup"])
		return
	_zb_t = clampf(_zb_t, 0.0, 1.0)
	_zb_pos()
	# pohupovani po pricli (0,3 m)
	head.position.y = EYE + sin(_zb_t * dl / 0.3 * PI) * 0.02
	_eye_y = head.position.y


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


## Diag (radce 20:00): cas _process meri obal, poradi behu hry se nemeni (drive diag _process prebiral).
func _process(_delta: float) -> void:
	var t_us := Time.get_ticks_usec()
	_process_vlastni(_delta)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("hrac", Time.get_ticks_usec() - t_us)


func _process_vlastni(_delta: float) -> void:
	_update_cam()


func _update_cam() -> void:
	if cam == null:
		return
	# poloha z interpolace fyziky, otoceni primo ze vstupu (bez zpozdeni)
	var o := get_global_transform_interpolated().origin if is_inside_tree() else global_position
	var bas := Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, pitch)
	cam.global_transform = Transform3D(bas, o + Vector3(0, _eye_y, 0) + Basis(Vector3.UP, yaw) * Vector3(head.position.x, 0, 0))


## Misa 0.89 (rybnik, tablet fyzika 43-63 ms): cas tohoto skriptu ve fyzice zvlast do diag (detail, nesecte se)
func _physics_process(delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	_fyz_krok(delta)
	var dg: Object = Engine.get_meta("diag", null)
	if dg:
		dg.cas("fyz: hrac", Time.get_ticks_usec() - t0)


func _fyz_krok(delta: float) -> void:
	_apply_rot()
	if na_koni != null:
		# poloha je sedlo (kun.gd ji nastavuje kazdy krok fyziky); oci jezdce nad sedlem
		_eye_y = lerpf(_eye_y, float(na_koni.get("OCI_NAD_SEDLEM")), minf(1.0, delta * 4.0))
		return
	if seated:
		_eye_y = lerpf(_eye_y, _seat_eye, minf(1.0, delta * 6.0))
		if move_input.length() > 0.5 or _jump:
			_jump = false
			stand_up()
		return
	if climbing:
		_lez(delta)
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
	if _vycerpan and vydrz >= BEH_ZNOVU_OD:
		_vycerpan = false
	if buh:
		vydrz = vydrz_max
		zivoty = ZIVOTY_MAX
		_vycerpan = false
	var run := beh and ml > 0.5 and slow > 0.9 and not _vycerpan and not flying
	# vydrz podle Dechu (dovednosti.json vloha_ucinky; hrac.json zavisi_na) - KCD2 Vitality
	var dv: Node = get_parent().get("dovednosti") if get_parent() else null
	var vmax := float(dv.call("ucinek", "vydrz_max", VYDRZ_MAX)) if dv else VYDRZ_MAX
	vydrz_max = vmax
	# vydrz: beh ji bere, po chvili bez behu se doplnuje; pri nule beh skonci (KCD2)
	if run:
		vydrz = maxf(0.0, vydrz - (float(dv.call("ucinek", "beh_za_s", BEH_ZA_S)) if dv else BEH_ZA_S) * delta)
		_beh_m += Vector2(velocity.x, velocity.z).length() * delta
		if _beh_m >= 100.0 and dv:
			_beh_m -= 100.0
			dv.call("udalost", "beh_100m")
		_bez_behu = 0.0
		if vydrz <= 0.0:
			_vycerpan = true
			beh = false
	else:
		_bez_behu += delta
		if _bez_behu > OBNOVA_PO_S:
			vydrz = minf(vmax, vydrz + OBNOVA_ZA_S * (OBNOVA_POHYB if ml > 0.15 else 1.0) * delta)
	run = run or (beh and ml > 0.5 and flying)
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
		if _jump and vydrz >= SKOK_VYDRZ:
			velocity.y = JUMP_V
			on_floor = false
			vydrz -= SKOK_VYDRZ                     # skok bere vydrz (KCD2 JumpCostBase)
			if dv:
				dv.call("udalost", "skok")
			_bez_behu = 0.0
	else:
		velocity.y -= _gravity * delta
	_jump = false
	var pre_vel := velocity
	var dg: Object = Engine.get_meta("diag", null)
	var tm := Time.get_ticks_usec()
	move_and_slide()
	var ts := Time.get_ticks_usec()
	# schod nebo prah: zkus se na nej vysunout
	if on_floor and is_on_wall() and Vector2(wish.x, wish.z).length() > 0.3:
		_step_up(Vector3(wish.x, 0, wish.z).normalized() * maxf(0.12, Vector2(pre_vel.x, pre_vel.z).length() * delta), pre_vel)
	if dg:
		# radce 17:10: rozdelit „fyz: hrac“ na move_and_slide / schod / zbytek skriptu
		dg.cas("fyz: hrac m&s", ts - tm)
		dg.cas("fyz: hrac schod", Time.get_ticks_usec() - ts)

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
		# pad (KCD2): do bez_skody nic, od zraneni_od ubira zivoty usporne az do smrt_od (pak 0); let a zebrik ne
		var vyska_padu := _air_y0 - global_position.y
		if not buh and not flying and not climbing and vyska_padu > float(PAD["zraneni_od_m"]):
			var k := clampf((vyska_padu - float(PAD["zraneni_od_m"])) / (float(PAD["smrt_od_m"]) - float(PAD["zraneni_od_m"])), 0.0, 1.0)
			zivoty = maxf(0.0, zivoty - ZIVOTY_MAX * k)
	if not floor_now:
		_air_y0 = maxf(_air_y0, global_position.y) if not _was_floor else global_position.y
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
	# nejdriv plny schod; pod nizkym stropem (dvere na pavlac hostince: 2,17 m, hrac 1,76 + 0,45 se nevesel)
	# i nizsi zvednuti, aby slo prekrocit prah a nizky schod
	for vy: float in SCHODY:
		if _zkus_schod(motion, pre_vel, vy):
			return


func _zkus_schod(motion: Vector3, pre_vel: Vector3, vy: float) -> bool:
	var xf := global_transform
	if test_move(xf, Vector3.UP * vy):
		return false
	var up := xf.translated(Vector3.UP * vy)
	if test_move(up, motion):
		return false
	var ahead := up.translated(motion)
	var col := KinematicCollision3D.new()
	if not test_move(ahead, Vector3.DOWN * (vy + 0.05), col):
		return false
	if col.get_normal().y < cos(floor_max_angle):
		return false
	var rise := vy - col.get_travel().length()
	if rise < 0.02:
		return false
	global_position = ahead.origin + col.get_travel()
	velocity.x = pre_vel.x
	velocity.z = pre_vel.z
	_land_kick = minf(0.05, _land_kick + rise * 0.15)
	return true


func _surface() -> String:
	if surface_at.is_valid():
		return surface_at.call(global_position)
	return "stone"


## Postavit hrace na nejblizsi volne misto s podlahou kolem p (hrac.json volne_misto): po sesednuti, slezeni
## zebriku, nacteni. Podlaha paprskem shora - cil muze byt pod terenem i v kolizi (kun, leseni).
func postav_na_volne(p0: Vector3) -> bool:
	var vm: Dictionary = Pravidla.cti("hrac", "volne_misto")
	var space := get_world_3d().direct_space_state
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = _col.shape
	q.exclude = [get_rid()]
	q.collision_mask = collision_mask
	var hy := float(vm["hledat_y_m"])
	# nejdriv jen podlaha v urovni ciloveho bodu (+-patro_m) ve vsech kruzich, az pak cokoli (test lezeni 29. 10.: ze
	# zebriku leseni v lomu hrac spadl na zem - kapsle na plosine narazila na tram, druhy kruh uz nasel teren dole)
	for patro: bool in [true, false]:
		if _postav_kruhy(p0, vm, space, q, hy, patro):
			return true
	global_position = p0
	velocity = Vector3.ZERO
	return false


func _postav_kruhy(p0: Vector3, vm: Dictionary, space: PhysicsDirectSpaceState3D, q: PhysicsShapeQueryParameters3D, hy: float, patro: bool) -> bool:
	for r: float in vm["polomery_m"]:
		var n := 1 if r == 0.0 else int(vm["smeru"])
		for k in n:
			var a := TAU * k / n
			var p := p0 + Vector3(cos(a) * r, 0.0, sin(a) * r)
			# v urovni patra paprsek jen od patro_m nad cilem (z hy nad cilem trefil plosinu leseni o patro vys)
			var nad := float(vm["patro_m"]) if patro else hy
			var down := PhysicsRayQueryParameters3D.create(p + Vector3(0, nad, 0), p - Vector3(0, hy, 0))
			down.exclude = [get_rid()]
			down.collision_mask = collision_mask
			var h := space.intersect_ray(down)
			if h.is_empty():
				continue
			if patro and absf(float((h["position"] as Vector3).y) - p0.y) > float(vm["patro_m"]):
				continue
			for dy: float in vm["vysky_m"]:
				var c := Vector3(p.x, float((h["position"] as Vector3).y) + dy, p.z)
				q.transform = Transform3D(Basis(), c + _col.position)
				if space.intersect_shape(q, 1).is_empty():
					global_position = c
					velocity = Vector3.ZERO
					return true
	return false
