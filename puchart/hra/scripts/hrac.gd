extends CharacterBody3D
## Hráč pro procházku (tablet + Xbox + PC). Dotyk: levá půlka = páčka chůze (tažením), pravá půlka = rozhled.
## Ovladač: levá páčka chůze, pravá rozhled, LT/RT = běh. PC: WASD + myš, Shift běh.
## Plné ovládání Havrana (pad.gd, menu) se převezme později – tady jen procházka pro prohlídku hradů a krajiny.

@export var rychlost := 1.6      # chůze ~1,6 m/s (KCD), běh 5 m/s
@export var beh := 5.0
var cam: Camera3D
var _yaw := 0.0
var yaw: float:   # Havranovy předměty (pokládání v pískovišti) čtou player.yaw
	get: return _yaw
var seated := false
var vydrz_max := 100.0
func stand_up() -> void: seated = false
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
# lezení po žebříku (Havran player.gd climb/_lez; Míša 14. 11.: „vem si z Havrana funkci lezení po žebříku“): postava na ose
# žebříku, páčka/dotyk nahoru a dolů, nahoře vystoupí na sestup, dole na nástup; páčka do strany = sestoupit. Pravidla hrac.json lezeni.
const Pravidla := preload("res://scripts/pravidla.gd")
var leze := false
var _zb: Dictionary = {}      # {pata, vrchol, nastup, sestup} ve světě (zebriky.gd, hlavni.zebriky)
var _zb_t := 0.0
var _col: CollisionShape3D

func _ready() -> void:
	cam = $Kamera
	_yaw = rotation.y
	for c in get_children():
		if c is CollisionShape3D: _col = c; break

func nastav_pohled(yaw: float, pitch := 0.0) -> void:
	_yaw = yaw; _pitch = pitch

func _input(e: InputEvent) -> void:
	if not is_physics_processing():
		return
	var w := get_viewport().get_visible_rect().size.x
	if e is InputEventScreenTouch:
		if e.pressed and ui.any(func(c): return c.is_visible_in_tree() and (c.ma_bod(e.position) if c.has_method("ma_bod") else c.get_global_rect().has_point(e.position))):
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

var _beh_packa := false
func _packa(ax: JoyAxis, ay: JoyAxis) -> Vector2:
	var v := Vector2(Input.get_joy_axis(0, ax), Input.get_joy_axis(0, ay)); var m := v.length()
	if m < 0.16: return Vector2.ZERO
	return v / m * minf(1.0, (m - 0.16) / 0.84)

func prepni_let() -> void:
	if leze: _konec_lezeni(Vector3.INF)
	leti = not leti
	collision_layer = 0 if leti else 1; collision_mask = 0 if leti else 1
	velocity = Vector3.ZERO

func _physics_process(dt: float) -> void:
	# ovladač
	# ovladač podle Havrana (pad.gd): mrtvá zóna 0,16 s plynulým náběhem, rozhled s křivkou (jemně u středu, rychle u kraje)
	var lp := _packa(JOY_AXIS_LEFT_X, JOY_AXIS_LEFT_Y); var rp := _packa(JOY_AXIS_RIGHT_X, JOY_AXIS_RIGHT_Y)
	if rp != Vector2.ZERO:
		var kr := rp * rp.length() * 2.7 * dt
		_yaw -= kr.x; _pitch = clampf(_pitch - kr.y * 0.8, -1.4, 1.4)
	rotation.y = _yaw
	cam.rotation.x = _pitch
	var v := Vector3(_pohyb.x, 0, _pohyb.y)
	if lp != Vector2.ZERO: v = Vector3(lp.x, 0, lp.y)
	elif _beh_packa: _beh_packa = false; bezi = false   # běh stiskem levé páčky končí zastavením (Havran)
	if Input.is_key_pressed(KEY_W): v.z -= 1
	if Input.is_key_pressed(KEY_S): v.z += 1
	if Input.is_key_pressed(KEY_A): v.x -= 1
	if Input.is_key_pressed(KEY_D): v.x += 1
	if leze:
		_lez(dt, v)
		return
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


## Chytit se žebříku (Havran player.climb): zb {pata, vrchol, nastup, sestup} ve světě; nahore = začít od vrcholu (slézání).
func chyt_zebrik(zb: Dictionary, nahore: bool) -> void:
	if leti: prepni_let()
	var lz: Dictionary = Pravidla.cti("hrac", "lezeni")
	_zb = zb
	_zb_t = float(lz["shora_t"]) if nahore else 0.0   # shora kousek pod vrchol: na 1,0 by hned vystoupil zpět (Havran 0.82)
	leze = true
	velocity = Vector3.ZERO
	autopilot = Vector3.INF
	if _col: _col.disabled = true
	var d := (zb["vrchol"] as Vector3) - (zb["pata"] as Vector3)
	if Vector2(d.x, d.z).length() > 0.05: _yaw = atan2(-d.x, -d.z)   # čelem k žebříku
	_pitch = 0.0
	_zb_pos()

func _zb_pos() -> void:
	var lz: Dictionary = Pravidla.cti("hrac", "lezeni")
	var a: Vector3 = _zb["pata"]; var b: Vector3 = _zb["vrchol"]
	var pred: Vector3 = (_zb["nastup"] as Vector3) - a   # postava před žebříkem (strana nástupu), oči nad příčlí
	pred.y = 0.0
	pred = pred.normalized() * float(lz["odstup_m"]) if pred.length() > 0.01 else Vector3.ZERO
	global_position = a.lerp(b, _zb_t) + pred - Vector3(0, float(lz["oci_pod_m"]), 0)

func _konec_lezeni(kam: Vector3) -> void:
	leze = false
	if _col: _col.disabled = false
	if kam != Vector3.INF: postav_na_volne(kam)
	velocity = Vector3.ZERO

## Krok lezení (Havran player._lez): v = vstup chůze (z < 0 dopředu = nahoru, x do strany = sestoupit vedle).
func _lez(dt: float, v: Vector3) -> void:
	var lz: Dictionary = Pravidla.cti("hrac", "lezeni")
	var a: Vector3 = _zb["pata"]; var b: Vector3 = _zb["vrchol"]
	var dl := maxf(a.distance_to(b), 0.5)
	var nah := clampf(-v.z, -1.0, 1.0)
	# Havran 0.88 „žebřík mě chytil a nemohl jsem odejít“: páčka do strany = dole na nástup, nahoře na sestup, uprostřed pustit se
	if absf(v.x) > float(lz["bok"]) and absf(v.x) > absf(nah):
		_konec_lezeni(_zb["nastup"] if _zb_t < 0.25 else (_zb["sestup"] if _zb_t > 0.75 else Vector3.INF))
		return
	_zb_t += nah * float(lz["rychlost_m_s"]) / dl * dt
	if _zb_t >= 1.0 and nah > 0.1:
		_konec_lezeni(_zb["sestup"]); return
	if _zb_t <= 0.0 and nah < -0.1:
		_konec_lezeni(_zb["nastup"]); return
	_zb_t = clampf(_zb_t, 0.0, 1.0)
	_zb_pos()

## Postavit hráče na nejbližší volné místo s podlahou kolem p0 (Havran player.postav_na_volne, hrac.json volne_misto):
## kruhy kolem cíle, podlaha paprskem shora, kapsle nad ní nesmí narazit; nejdřív jen podlaha v úrovni cíle (±patro_m).
func postav_na_volne(p0: Vector3) -> bool:
	var vm: Dictionary = Pravidla.cti("hrac", "volne_misto")
	var space := get_world_3d().direct_space_state
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = _col.shape; q.exclude = [get_rid()]; q.collision_mask = collision_mask
	for patro: bool in [true, false]:
		for r: float in vm["polomery_m"]:
			var n := 1 if r == 0.0 else int(vm["smeru"])
			for k in n:
				var u := TAU * k / n
				var p := p0 + Vector3(cos(u) * r, 0.0, sin(u) * r)
				var nad := float(vm["patro_m"]) if patro else float(vm["hledat_y_m"])   # v úrovni patra paprsek jen od patro_m nad cílem
				var dolu := PhysicsRayQueryParameters3D.create(p + Vector3(0, nad, 0), p - Vector3(0, float(vm["hledat_y_m"]), 0))
				dolu.exclude = [get_rid()]; dolu.collision_mask = collision_mask
				var h := space.intersect_ray(dolu)
				if h.is_empty(): continue
				var hy := float((h["position"] as Vector3).y)
				if patro and absf(hy - p0.y) > float(vm["patro_m"]): continue
				for dy: float in vm["vysky_m"]:
					var c := Vector3(p.x, hy + dy, p.z)
					q.transform = Transform3D(Basis(), c + _col.position)
					if space.intersect_shape(q, 1).is_empty():
						global_position = c; velocity = Vector3.ZERO
						return true
	global_position = p0; velocity = Vector3.ZERO
	return false
