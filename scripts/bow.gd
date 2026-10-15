extends Node3D
## Luk v ruce: napinani, vystrel, let sipu s gravitaci, zapichnuti a body za terce.

signal scored(points: int, total: int, text: String)

const Batch := preload("res://scripts/mesh_batch.gd")
const DRAW_TIME := 0.85
const MAX_STUCK := 24
const GRAVITY := 9.81

var equipped := false
var drawing := false
var draw := 0.0
var total := 0
var shots := 0

var player: CharacterBody3D
var cam: Camera3D
var life: Node
var world: Node3D
var targets: Array = []

var _view: Node3D            # luk pred kamerou
var _nock: Node3D            # sip na tetive
var _str_a: MeshInstance3D
var _str_b: MeshInstance3D
var _arrow_tpl: Node3D
var _flying: Array = []      # {node, vel, life}
var _stuck: Array = []
var _equip_t := 0.0
var _base_fov := 72.0
var _kick := 0.0


func setup(p_player: CharacterBody3D, p_life: Node, p_world: Node3D, mats: Dictionary, props: RefCounted, p_targets: Array) -> void:
	player = p_player
	cam = player.cam
	life = p_life
	world = p_world
	targets = p_targets
	_base_fov = cam.fov
	# luk pro pohled z prvni osoby
	_view = Node3D.new()
	_view.name = "LukVRuce"
	cam.add_child(_view)
	var b := Batch.new(mats, 77)
	props.bow(b, Transform3D.IDENTITY, false)
	var vm := b.commit(_view, "Luk", false)
	for c in vm.get_children():
		if c is GeometryInstance3D:
			(c as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_str_a = _string_piece()
	_str_b = _string_piece()
	# sablona sipu: hrot miri do -Z
	var ab := Batch.new(mats, 78)
	props.arrow(ab, Vector3(0, 0, 0.42), Vector3(0, 0, -0.38))
	_arrow_tpl = ab.commit(self, "SablonaSipu", false)
	_arrow_tpl.visible = false
	_nock = _arrow_tpl.duplicate()
	_nock.visible = true
	_view.add_child(_nock)
	_view.visible = false
	set_physics_process(true)


func _string_piece() -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.0022
	cm.bottom_radius = 0.0022
	cm.height = 1.0
	cm.radial_segments = 4
	cm.rings = 1
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.86, 0.83, 0.74)
	m.roughness = 0.8
	cm.material = m
	mi.mesh = cm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_view.add_child(mi)
	return mi


func equip(on: bool) -> void:
	equipped = on
	drawing = false
	draw = 0.0
	_equip_t = 0.0
	_view.visible = on
	player.slow = 1.0
	cam.fov = _base_fov


func begin_draw() -> void:
	if not equipped or drawing:
		return
	drawing = true
	life.sfx("luk_napnout", -4.0, randf_range(0.95, 1.05))


func release() -> void:
	if not equipped or not drawing:
		return
	drawing = false
	if draw < 0.18:
		draw = 0.0
		return
	var speed := 16.0 + 46.0 * draw
	var dir := -cam.global_transform.basis.z
	var a: Node3D = _arrow_tpl.duplicate()
	a.visible = true
	world.add_child(a)
	var start := cam.global_position + dir * 0.4 + cam.global_transform.basis.y * -0.03
	a.global_position = start
	a.look_at(start + dir, Vector3.UP if absf(dir.y) < 0.98 else Vector3.FORWARD)
	_flying.append({"node": a, "vel": dir * speed, "life": 6.0})
	life.sfx("luk_vystrel", -2.0, randf_range(0.95, 1.06))
	shots += 1
	draw = 0.0
	_kick = 1.0


func _process(delta: float) -> void:
	if not equipped:
		return
	_equip_t = minf(1.0, _equip_t + delta * 3.0)
	if drawing:
		draw = minf(1.0, draw + delta / DRAW_TIME)
	_kick = maxf(0.0, _kick - delta * 5.0)
	player.slow = 1.0 - draw * (1.0 - player.DRAW_SLOW)
	cam.fov = lerpf(cam.fov, _base_fov - 12.0 * draw, minf(1.0, delta * 8.0))
	var e := 1.0 - pow(1.0 - _equip_t, 3.0)
	# poloha luku: v klidu sklopeny vlevo dole, pri napinani vzhuru na stred
	var rest := Transform3D(Basis.from_euler(Vector3(deg_to_rad(-8), deg_to_rad(10), deg_to_rad(38))), Vector3(-0.30, -0.44, -0.72))
	var aim := Transform3D(Basis.from_euler(Vector3(0.0, deg_to_rad(2), deg_to_rad(14))), Vector3(-0.10, -0.07, -0.74))
	var w := smoothstep(0.0, 1.0, minf(1.0, draw * 1.6))
	var t := rest.interpolate_with(aim, w)
	t.origin += Vector3(0, -0.5 * (1.0 - e), 0)
	t.origin.z += _kick * 0.04
	var sway := Vector3(sin(Time.get_ticks_msec() * 0.0011), sin(Time.get_ticks_msec() * 0.0017), 0) * 0.004 * w
	t.origin += sway
	_view.transform = t
	# tetiva a sip: tetiva se natahuje k oku
	var pull := 0.05 + 0.33 * draw
	var nock := Vector3(0, 0, pull)
	_set_string(_str_a, Vector3(0, 0.82, 0), nock)
	_set_string(_str_b, Vector3(0, -0.82, 0), nock)
	_nock.visible = drawing or draw > 0.0 or _kick < 0.2
	_nock.transform = Transform3D(Basis.IDENTITY, nock + Vector3(0, 0, -0.42))


func _set_string(mi: MeshInstance3D, a: Vector3, b: Vector3) -> void:
	var mid := (a + b) * 0.5
	var d := b - a
	var len := d.length()
	var y := d / len
	var x := y.cross(Vector3(0, 0, 1))
	if x.length() < 0.01:
		x = Vector3(1, 0, 0)
	x = x.normalized()
	var z := x.cross(y).normalized()
	mi.transform = Transform3D(Basis(x, y * len, z), mid)


func _physics_process(delta: float) -> void:
	if _flying.is_empty():
		return
	var space := get_world_3d().direct_space_state
	for i in range(_flying.size() - 1, -1, -1):
		var f: Dictionary = _flying[i]
		var node: Node3D = f["node"]
		var vel: Vector3 = f["vel"]
		vel.y -= GRAVITY * delta
		var prev := node.global_position
		var next := prev + vel * delta
		var q := PhysicsRayQueryParameters3D.create(prev, next)
		q.exclude = [player.get_rid()]
		var hit := space.intersect_ray(q)
		f["life"] -= delta
		if not hit.is_empty():
			var dir := vel.normalized()
			var p: Vector3 = hit["position"]
			node.global_position = p - dir * 0.3
			node.look_at(node.global_position + dir, Vector3.UP if absf(dir.y) < 0.98 else Vector3.FORWARD)
			_flying.remove_at(i)
			_stick(node)
			_score(p)
			continue
		if f["life"] <= 0.0:
			node.queue_free()
			_flying.remove_at(i)
			continue
		node.global_position = next
		if vel.length() > 0.1:
			node.look_at(next + vel, Vector3.UP if absf(vel.normalized().y) < 0.98 else Vector3.FORWARD)
		f["vel"] = vel


func _stick(node: Node3D) -> void:
	_stuck.append(node)
	if _stuck.size() > MAX_STUCK:
		var old: Node3D = _stuck.pop_front()
		old.queue_free()


func _score(p: Vector3) -> void:
	for t: Dictionary in targets:
		var c: Vector3 = t["center"]
		var n: Vector3 = t["normal"]
		var off := p - c
		var dp := off.dot(n)
		if absf(dp) > 0.35:
			continue
		var r := (off - n * dp).length() / float(t["radius"])
		if r > 1.03:
			continue
		var pts := 10 if r <= 0.2 else (8 if r <= 0.4 else (6 if r <= 0.6 else (4 if r <= 0.8 else 2)))
		total += pts
		var txt := "Střed! %d bodů" % pts if pts == 10 else "Zásah: %d %s" % [pts, "body" if pts <= 4 else "bodů"]
		life.sfx("sip_zasah_terc", 0.0, randf_range(0.95, 1.05), p)
		scored.emit(pts, total, txt)
		return
	life.sfx("sip_zasah_drevo", -3.0, randf_range(0.9, 1.1), p)
	scored.emit(0, total, "Vedle")
