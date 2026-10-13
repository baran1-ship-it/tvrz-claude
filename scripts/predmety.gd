extends Node
## Predmety ve svete a v brasne: katalog (modely/predmety.json), inventar hrace, polozene predmety
## (truhly s obsahem, lavice, sudy...), rezim pokladani v piskovisti a ulozeni do hry.

const KATALOG := "res://modely/predmety.json"
const DIR := "res://modely/predmety/"

var main: Node
var kat: Dictionary = {}            # id -> {nazev, kat, stav, vaha, cena, rozmer, kont?, sed?, lehat?}
var inv: Dictionary = {}            # id -> pocet (brasna hrace)
var placed: Array = []              # [{id, p: Vector3, yaw: float, obsah: {id: pocet}, node: Node3D}]
var _scenes: Dictionary = {}
var _icons: Dictionary = {}
var root: Node3D

# pokladani
var placing := ""
var _ghost: Node3D
var _gyaw := 0.0
var _gdist := 2.0
var _ui: CanvasLayer
var _from_inv := false
var _moving: Dictionary = {}       # presouvany polozeny predmet (pri zruseni se vrati na misto)
var _valid := true
var _wall := false
var _wall_yaw := 0.0
var _bad_mat: StandardMaterial3D


func setup(p_main: Node, world: Node3D) -> void:
	main = p_main
	var f := FileAccess.open(KATALOG, FileAccess.READ)
	if f:
		kat = JSON.parse_string(f.get_as_text())
	root = Node3D.new()
	root.name = "Predmety"
	world.add_child(root)
	_build_place_ui()


func icon(id: String) -> Texture2D:
	if not _icons.has(id):
		_icons[id] = load(DIR + id + ".png")
	return _icons[id]


func scene(id: String) -> PackedScene:
	if not _scenes.has(id):
		_scenes[id] = load(DIR + id + ".glb")
	return _scenes[id]


func name_of(id: String) -> String:
	return String(kat.get(id, {}).get("nazev", id))


func weight(items: Dictionary) -> float:
	var w := 0.0
	for id: String in items:
		w += float(kat.get(id, {}).get("vaha", 0.0)) * int(items[id])
	return w


func add_inv(id: String, n: int = 1) -> void:
	inv[id] = int(inv.get(id, 0)) + n
	if int(inv[id]) <= 0:
		inv.erase(id)


func start_kit() -> void:
	# pocatecni vybava do piskoviste
	inv = {"sekera": 1, "stit": 1, "lucerna": 1, "miska": 2, "lzice": 2, "talir": 2, "kosik": 1}


# ------------------------------------------------------------------ polozene predmety

func ground_y(x: float, z: float, top := 3.0) -> float:
	var space := root.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(Vector3(x, top, z), Vector3(x, top - 8.0, z))
	var h := space.intersect_ray(q)
	return float((h["position"] as Vector3).y) if not h.is_empty() else 0.0


func spawn_on_wall(id: String, from: Vector3, dir: Vector3, extra := {}) -> void:
	# vychozi vybaveni: predmet na zed, kam dopadne vodorovny paprsek
	var space := root.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(from, from + dir * 6.0)
	var h := space.intersect_ray(q)
	if h.is_empty():
		return
	var nrm: Vector3 = h["normal"]
	var r: Array = kat.get(id, {}).get("rozmer", [0.2, 0.2, 0.2])
	var yaw := atan2(nrm.x, nrm.z)
	var p: Vector3 = (h["position"] as Vector3) + nrm * float(r[2]) * 0.5 - Vector3.UP * float(r[1]) * 0.5
	var rec := {"id": id, "p": p, "yaw": yaw, "spin": 0.0, "obsah": {}}
	rec.merge(extra)
	spawn(rec)


func spawn(rec: Dictionary) -> void:
	var id: String = rec["id"]
	var info: Dictionary = kat.get(id, {})
	var n := Node3D.new()
	n.position = rec["p"]
	n.rotation.y = float(rec["yaw"])
	root.add_child(n)
	if rec.has("spin"):
		n.rotate_object_local(Vector3.BACK, float(rec["spin"]))
	var m: Node3D = scene(id).instantiate()
	n.add_child(m)
	if info.get("louc", false):
		if not rec.has("louc"):
			rec["louc"] = true
			rec["hori"] = true
		_bracket_torch(rec, n)
	rec["node"] = n
	if SVETLA.has(id):
		_light_fx(rec)
	var r: Array = info.get("rozmer", [0.5, 0.5, 0.5])
	# kolize jen u vetsich veci (o drobnosti se hrac nezakopne)
	if (float(r[1]) > 0.25 or float(r[0]) > 0.6) and not info.get("zed", false):
		var b := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = Vector3(float(r[0]), float(r[1]), float(r[2])) * 0.95
		cs.shape = bs
		cs.position.y = float(r[1]) * 0.5
		b.add_child(cs)
		n.add_child(b)
	rec["node"] = n
	placed.append(rec)
	_refresh_use()


func remove(rec: Dictionary) -> void:
	_torch_off(rec)
	if rec.has("node"):
		(rec["node"] as Node3D).queue_free()
	placed.erase(rec)
	_refresh_use()


func _refresh_use() -> void:
	var use: Array = main.info["use"]
	for i in range(use.size() - 1, -1, -1):
		if String(use[i].get("kind", "")) == "predmet":
			use.remove_at(i)
	for rec: Dictionary in placed:
		var r: Array = kat.get(rec["id"], {}).get("rozmer", [0.5, 0.5, 0.5])
		use.append({"kind": "predmet", "rec": rec, "pos": (rec["p"] as Vector3) + Vector3(0, minf(float(r[1]), 1.2), 0),
				"r": 1.6 + maxf(float(r[0]), float(r[2])) * 0.5})


func _small(id: String) -> bool:
	# drobnost, kterou lze vzit do brasny (ne nabytek)
	var info: Dictionary = kat.get(id, {})
	return info.get("kat", null) != null and float(info.get("vaha", 99)) < 15.0 and not info.get("sed", false)


# svitici predmety: [plamen v lokalnich souradnicich modelu, velikost plamene, sila svetla, dosah, poloha v ruce]
const SVETLA := {
	"louc": [Vector3(0, 0.56, 0), 0.42, 1.8, 9.0, Vector3(0.32, -0.42, -0.62)],
	"lucerna": [Vector3(0, 0.2, 0), 0.13, 2.2, 9.5, Vector3(0.36, -0.72, -0.7)],
	"svicen": [Vector3(0, 0.225, 0), 0.09, 0.75, 4.5, Vector3(0.28, -0.45, -0.55)],
	"svicny": [Vector3(0, 0.86, 0), 0.12, 1.2, 6.0, Vector3(0.3, -0.95, -0.7)],
}

var held_id := ""                  # co hrac nese v ruce (louc, lucerna, svicen...)
var held_lit := false
var held_torch: bool:
	get:
		return held_id == "louc"
var _hand: Node3D
var _hand_fx: Dictionary = {}


func use_label(u: Dictionary) -> String:
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if info.get("louc", false):
		if bool(rec.get("louc", false)):
			return "" if held_id != "" else "Vzít louč"
		return "Vložit louč" if held_torch else ""
	if SVETLA.has(rec["id"]):
		return "" if held_id != "" else "Vzít do ruky: %s" % name_of(rec["id"])
	if info.has("kont"):
		return "Otevřít: %s" % name_of(rec["id"])
	if info.get("lehat", false):
		return "Lehnout si"
	if info.get("sed", false):
		return "Sednout si"
	if _small(rec["id"]):
		return "Vzít: %s" % name_of(rec["id"])
	return ""


func use(u: Dictionary) -> void:
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if info.get("louc", false):
		if bool(rec.get("louc", false)) and held_id == "":
			rec["louc"] = false
			hold("louc", bool(rec.get("hori", true)))
			_bracket_torch(rec, rec["node"])
			main.life.sfx("presun", -6.0)
		elif not bool(rec.get("louc", false)) and held_torch:
			rec["louc"] = true
			rec["hori"] = held_lit
			hold("", false)
			_bracket_torch(rec, rec["node"])
			main.life.sfx("polozit", -8.0)
		return
	if SVETLA.has(rec["id"]):
		if held_id == "":
			hold(rec["id"], bool(rec.get("hori", false)))
			remove(rec)
			main.life.sfx("presun", -6.0)
		return
	if info.has("kont"):
		main.life.sfx("otevrit", -4.0)
		main.open_container(rec)
		return
	if info.get("sed", false) or info.get("lehat", false):
		var r: Array = info.get("rozmer", [0.5, 0.5, 0.5])
		var pl: CharacterBody3D = main.player
		var back := pl.global_position
		if info.get("lehat", false):
			# lehnout na postel a nabidnout spanek
			pl.sit((rec["p"] as Vector3) + Vector3(0, 0.15, 0), 0.62, back, pl.yaw, deg_to_rad(55))
			main.offer_sleep()
		else:
			var seat_h := minf(float(r[1]), 0.5) if float(r[1]) > 0.3 else float(r[1])
			pl.sit(rec["p"], seat_h + 0.78, back, pl.yaw + PI)
		main.life.sfx("presun", -10.0, 0.7)
		return
	if _small(rec["id"]):
		add_inv(rec["id"])
		_drop_contents(rec)
		remove(rec)
		main.life.sfx("presun", -6.0)
		main.hud.toast("%s – do brašny" % name_of(rec["id"]), 1.4)


func drop_label() -> String:
	return "Odložit: %s" % name_of(held_id) if held_id != "" else ""


func drop_held() -> void:
	# polozit nesene svetlo pred sebe na zem (hori dal, pokud horelo)
	if held_id == "":
		return
	var pl: CharacterBody3D = main.player
	var f: Vector3 = -(pl.cam as Camera3D).global_transform.basis.z
	f.y = 0.0
	var p: Vector3 = pl.global_position + f.normalized() * 0.8
	p.y = ground_y(p.x, p.z, pl.global_position.y + 1.2)
	var rec := {"id": held_id, "p": p, "yaw": pl.yaw, "obsah": {}, "hori": held_lit}
	hold("", false)
	spawn(rec)
	main.life.sfx("polozit", -8.0)


func use2_label(u: Dictionary) -> String:
	# X: zapalit / zhasnout svetlo v ruce, v drzaku nebo polozene
	if held_id != "":
		return "Zhasnout" if held_lit else "Zapálit"
	if not u.is_empty() and String(u.get("kind", "")) == "predmet":
		var rec: Dictionary = u["rec"]
		if bool(rec.get("louc", false)) or SVETLA.has(rec["id"]):
			return "Zhasnout" if bool(rec.get("hori", false)) else "Zapálit"
	return ""


func use2(u: Dictionary) -> void:
	if held_id != "":
		hold(held_id, not held_lit)
		main.life.sfx("whoosh", -8.0, 1.3 if held_lit else 0.8)
		return
	if not u.is_empty() and String(u.get("kind", "")) == "predmet":
		var rec: Dictionary = u["rec"]
		if bool(rec.get("louc", false)):
			rec["hori"] = not bool(rec.get("hori", false))
			_bracket_torch(rec, rec["node"])
		elif SVETLA.has(rec["id"]):
			rec["hori"] = not bool(rec.get("hori", false))
			_light_fx(rec)
		else:
			return
		main.life.sfx("whoosh", -8.0, 1.3 if rec["hori"] else 0.8)


# ------------------------------------------------------------------ louce a svetla

func _fire_fx(parent: Node3D, local_tip: Vector3, energy: float, rng: float, size := 0.42) -> Dictionary:
	# plamen (castice ve svetovych souradnicich, tahnou se za pohybem) a mihotave svetlo se stiny
	var tip := Node3D.new()
	tip.position = local_tip
	parent.add_child(tip)
	var fl: CPUParticles3D = main.life._flames(Vector3.ZERO, size, 14 if size > 0.3 else 8, 0.5 if size > 0.3 else 0.35)
	fl.get_parent().remove_child(fl)
	tip.add_child(fl)
	fl.position = Vector3.ZERO
	var l := OmniLight3D.new()
	l.light_color = main.life.FIRE_COL
	l.light_energy = energy
	l.omni_range = rng
	l.omni_attenuation = 1.4
	l.shadow_enabled = main.quality >= 1
	l.shadow_bias = 0.06
	l.shadow_normal_bias = 1.2
	l.position = Vector3(0, 0.15 if size > 0.3 else 0.05, 0)
	tip.add_child(l)
	var ld := {"light": l, "base": energy, "phase": randf() * 50.0, "speed": randf_range(8.0, 12.0),
			"night_only": false, "fx": [fl], "shadow": true}
	main.life.lights.append(ld)
	return {"tip": tip, "ld": ld}


func _kill_fx(fx: Dictionary) -> void:
	if fx.is_empty():
		return
	main.life.lights.erase(fx["ld"])
	(fx["tip"] as Node3D).queue_free()


func _torch_off(rec: Dictionary) -> void:
	if rec.has("_fx"):
		_kill_fx(rec["_fx"])
		rec.erase("_fx")
	if rec.has("_louc") and is_instance_valid(rec["_louc"]):
		(rec["_louc"] as Node3D).queue_free()
	rec.erase("_louc")


func _light_fx(rec: Dictionary) -> void:
	# polozena lucerna, svicen...: plamen podle stavu
	if rec.has("_fx"):
		_kill_fx(rec["_fx"])
		rec.erase("_fx")
	if bool(rec.get("hori", false)) and rec.has("node"):
		var sv: Array = SVETLA[rec["id"]]
		rec["_fx"] = _fire_fx(rec["node"], sv[0], sv[2], sv[3], sv[1])


func _bracket_torch(rec: Dictionary, n: Node3D) -> void:
	# louc v drzaku (objimka 6 cm od zdi), pripadne horici
	_torch_off(rec)
	if not bool(rec.get("louc", false)):
		return
	var t: Node3D = scene("louc").instantiate()
	t.position = Vector3(0, -0.03, 0.057)
	t.rotation.x = deg_to_rad(12)
	n.add_child(t)
	rec["_louc"] = t
	if bool(rec.get("hori", false)):
		rec["_fx"] = _fire_fx(t, Vector3(0, 0.56, 0), 1.6, 7.5)


func hold(id: String, lit: bool) -> void:
	# svetlo v ruce: vpravo dole pred kamerou, plamen se pohupuje s chuzi a tahne se za pohybem
	if _hand:
		_kill_fx(_hand_fx)
		_hand_fx = {}
		_hand.queue_free()
		_hand = null
	held_id = id
	held_lit = lit and id != ""
	if id == "":
		return
	var sv: Array = SVETLA[id]
	_hand = Node3D.new()
	_hand.position = sv[4]
	_hand.rotation = Vector3(deg_to_rad(-14 if id == "louc" else -4), 0, deg_to_rad(-8 if id == "louc" else 0))
	main.player.cam.add_child(_hand)
	var t: Node3D = scene(id).instantiate()
	_hand.add_child(t)
	for mi in t.find_children("*", "GeometryInstance3D", true, false):
		(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	if held_lit:
		_hand_fx = _fire_fx(_hand, sv[0], sv[2] * 1.1, sv[3] * 1.15, sv[1])


func _hold_torch(on: bool, lit: bool) -> void:
	hold("louc" if on else "", lit)


func delete(rec: Dictionary) -> void:
	# stavebni rezim: odstranit predmet (obsah truhly se presune do brasny)
	var n := _drop_contents(rec)
	remove(rec)
	main.life.sfx("polozit", -8.0, 0.8)
	main.hud.toast("Odstraněno" + (" – obsah je v brašně" if n > 0 else ""), 1.6)


func _drop_contents(rec: Dictionary) -> int:
	var n := 0
	var ob: Dictionary = rec.get("obsah", {})
	for id: String in ob:
		add_inv(id, int(ob[id]))
		n += int(ob[id])
	rec["obsah"] = {}
	return n


func nearest(cam: Camera3D) -> Dictionary:
	# nejblizsi polozeny predmet, na ktery se hrac diva (pro stavebni rezim)
	var best := {}
	var best_d := 1e9
	var eye := cam.global_position
	var fwd := -cam.global_transform.basis.z
	for u: Dictionary in main.info["use"]:
		if String(u.get("kind", "")) != "predmet":
			continue
		var to: Vector3 = (u["pos"] as Vector3) - eye
		var d := to.length()
		if d > float(u["r"]) + 1.0 or (d > 0.9 and fwd.dot(to / d) < 0.6):
			continue
		if d < best_d:
			best_d = d
			best = u
	return best


# ------------------------------------------------------------------ pokladani (piskoviste)

func begin_place(id: String, from_inv: bool) -> void:
	cancel_place()
	placing = id
	_from_inv = from_inv
	_ghost = scene(id).instantiate()
	root.add_child(_ghost)
	for mi in _ghost.find_children("*", "GeometryInstance3D", true, false):
		(mi as GeometryInstance3D).transparency = 0.35
		(mi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var r: Array = kat.get(id, {}).get("rozmer", [0.5, 0.5, 0.5])
	_gdist = 1.3 + maxf(float(r[0]), float(r[2])) * 0.7
	_gyaw = 0.0
	_valid = true
	_ui.visible = true


func begin_move(rec: Dictionary) -> void:
	# zvednout polozeny predmet a hned ho pokladat jinam (obsah truhly zustava)
	var keep := rec.duplicate()
	remove(rec)
	keep.erase("node")
	begin_place(String(keep["id"]), false)
	_moving = keep
	_gyaw = float(keep["yaw"]) - (main.player.yaw + PI)


func cancel_place() -> void:
	if not _moving.is_empty():
		var back := _moving
		_moving = {}
		spawn(back)
	if _ghost:
		_ghost.queue_free()
	_ghost = null
	placing = ""
	if _ui:
		_ui.visible = false


func rotate_place(step: float) -> void:
	_gyaw += step


func confirm_place() -> void:
	if placing == "" or _ghost == null:
		return
	if not _valid:
		main.hud.toast("Tady to nejde postavit", 1.2)
		return
	var rec := {"id": placing, "p": _ghost.global_position, "yaw": _ghost.rotation.y, "obsah": {}}
	if _wall:
		rec["yaw"] = _wall_yaw
		rec["spin"] = _gyaw
	if not _moving.is_empty():
		rec["obsah"] = _moving.get("obsah", {})
		_moving = {}
		spawn(rec)
		main.life.sfx("polozit", -6.0)
		cancel_place()
		return
	if _from_inv:
		add_inv(placing, -1)
	spawn(rec)
	main.life.sfx("polozit", -6.0)
	var id := placing
	cancel_place()
	# z katalogu stavění lze klast dalsi kus hned
	if not _from_inv:
		begin_place(id, false)


func _process(_delta: float) -> void:
	if _ghost == null or main.player == null:
		return
	var cam: Camera3D = main.player.cam
	var fwd := -cam.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized()
	var p: Vector3 = main.player.global_position + fwd * _gdist
	# zem paprskem shora (prochazi pres podlahy, vybere prvni povrch pod urovni oci)
	var space := root.get_world_3d().direct_space_state
	var r0: Array = kat.get(placing, {}).get("rozmer", [0.5, 0.5, 0.5])
	if kat.get(placing, {}).get("zed", false):
		# predmet na zed: paprsek z oci, zavesi se na svislou plochu (stred na miste, kam hrac miri)
		var eye := cam.global_position
		var wq := PhysicsRayQueryParameters3D.create(eye, eye - cam.global_transform.basis.z * 3.5)
		wq.exclude = [main.player.get_rid()]
		var wh := space.intersect_ray(wq)
		_wall = not wh.is_empty() and absf((wh["normal"] as Vector3).y) < 0.35
		if _wall:
			var nrm: Vector3 = wh["normal"]
			_wall_yaw = atan2(nrm.x, nrm.z)
			var b := Basis(Vector3.UP, _wall_yaw).rotated(nrm, _gyaw)
			_ghost.global_transform = Transform3D(b, (wh["position"] as Vector3) + nrm * float(r0[2]) * 0.5 - b.y * float(r0[1]) * 0.5)
			_set_valid(true)
			return
	_wall = false
	var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.6, 0), p + Vector3(0, -3.0, 0))
	q.exclude = [main.player.get_rid()]
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		p = hit["position"]
	_ghost.global_position = p
	_ghost.rotation.y = main.player.yaw + PI + _gyaw
	# kontrola mista: kvadr predmetu (bez spodnich 6 cm) nesmi zasahovat do zdi ani jinych veci
	var r: Array = kat.get(placing, {}).get("rozmer", [0.5, 0.5, 0.5])
	var bs := BoxShape3D.new()
	bs.size = Vector3(float(r[0]) * 0.85, maxf(0.02, float(r[1]) - 0.08), float(r[2]) * 0.85)
	var sq := PhysicsShapeQueryParameters3D.new()
	sq.shape = bs
	var lift := 0.06 + 0.08 * maxf(float(r[0]), float(r[2]))      # mirny svah pod predmetem nevadi
	sq.transform = Transform3D(Basis(Vector3.UP, _ghost.rotation.y), p + Vector3(0, lift + bs.size.y * 0.5, 0))
	sq.exclude = [main.player.get_rid()]
	_set_valid(space.intersect_shape(sq, 1).is_empty())


func _set_valid(ok: bool) -> void:
	if ok != _valid:
		_valid = ok
		if _bad_mat == null:
			_bad_mat = StandardMaterial3D.new()
			_bad_mat.albedo_color = Color(1.0, 0.15, 0.1, 0.45)
			_bad_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			_bad_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		for mi in _ghost.find_children("*", "GeometryInstance3D", true, false):
			(mi as GeometryInstance3D).material_overlay = null if ok else _bad_mat


func _build_place_ui() -> void:
	# dotykove ovladani pokladani; na ovladaci: LT/RT otocit, A polozit, B zrusit
	_ui = CanvasLayer.new()
	_ui.layer = 6
	_ui.visible = false
	add_child(_ui)
	var box := HBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	box.position = Vector2(-330, -150)
	box.add_theme_constant_override("separation", 14)
	_ui.add_child(box)
	var font: Font = load("res://fonts/GrenzeGotisch-Medium.ttf")
	for it: Array in [["⟲  LT", func() -> void: rotate_place(PI / 8)], ["Položit  A", confirm_place],
			["Zrušit  B", cancel_place], ["RT  ⟳", func() -> void: rotate_place(-PI / 8)]]:
		var b := Button.new()
		b.text = it[0]
		b.custom_minimum_size = Vector2(150, 64)
		b.add_theme_font_override("font", font)
		b.add_theme_font_size_override("font_size", 28)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.1, 0.08, 0.06, 0.8)
		sb.border_color = Color(0.85, 0.68, 0.38)
		sb.set_border_width_all(2)
		sb.set_corner_radius_all(6)
		b.add_theme_stylebox_override("normal", sb)
		b.add_theme_stylebox_override("hover", sb)
		b.add_theme_stylebox_override("pressed", sb)
		b.add_theme_color_override("font_color", Color(0.95, 0.88, 0.7))
		b.focus_mode = Control.FOCUS_NONE
		b.pressed.connect(it[1])
		box.add_child(b)


# ------------------------------------------------------------------ ulozeni

func to_save() -> Dictionary:
	var arr := []
	for rec: Dictionary in placed:
		var p: Vector3 = rec["p"]
		var d := {"id": rec["id"], "p": [p.x, p.y, p.z], "yaw": rec["yaw"], "obsah": rec.get("obsah", {})}
		for k: String in ["spin", "louc", "hori"]:
			if rec.has(k):
				d[k] = rec[k]
		arr.append(d)
	return {"inv": inv, "polozene": arr, "v_ruce": held_id, "v_ruce_hori": held_lit}


func from_save(j: Dictionary) -> void:
	for rec: Dictionary in placed.duplicate():
		remove(rec)
	inv = {}
	for id: String in j.get("inv", {}):
		if kat.has(id):
			inv[id] = int(j["inv"][id])
	for r: Dictionary in j.get("polozene", []):
		if not kat.has(String(r["id"])):
			continue
		var a: Array = r["p"]
		var obsah := {}
		for id: String in r.get("obsah", {}):
			obsah[id] = int(r["obsah"][id])
		var rec := {"id": String(r["id"]), "p": Vector3(a[0], a[1], a[2]), "yaw": float(r["yaw"]), "obsah": obsah}
		for k: String in ["spin", "louc", "hori"]:
			if r.has(k):
				rec[k] = r[k]
		spawn(rec)
	hold(String(j.get("v_ruce", "")), bool(j.get("v_ruce_hori", false)))
