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

func spawn(rec: Dictionary) -> void:
	var id: String = rec["id"]
	var info: Dictionary = kat.get(id, {})
	var n := Node3D.new()
	n.position = rec["p"]
	n.rotation.y = float(rec["yaw"])
	root.add_child(n)
	var m: Node3D = scene(id).instantiate()
	n.add_child(m)
	var r: Array = info.get("rozmer", [0.5, 0.5, 0.5])
	# kolize jen u vetsich veci (o drobnosti se hrac nezakopne)
	if float(r[1]) > 0.25 or float(r[0]) > 0.6:
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


func use_label(u: Dictionary) -> String:
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if info.has("kont"):
		return "Otevřít: %s" % name_of(rec["id"])
	return "Zvednout: %s" % name_of(rec["id"])


func use(u: Dictionary) -> void:
	var rec: Dictionary = u["rec"]
	var info: Dictionary = kat.get(rec["id"], {})
	if info.has("kont"):
		main.life.sfx("otevrit", -4.0)
		main.open_container(rec)
		return
	# zvednout do brasny (jen piskoviste)
	if main.mode == "piskoviste":
		add_inv(rec["id"])
		remove(rec)
		main.hud.toast("%s – do brašny" % name_of(rec["id"]), 1.4)


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
	_ui.visible = true


func cancel_place() -> void:
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
	var rec := {"id": placing, "p": _ghost.global_position, "yaw": _ghost.rotation.y, "obsah": {}}
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
	var q := PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.6, 0), p + Vector3(0, -3.0, 0))
	q.exclude = [main.player.get_rid()]
	var hit := space.intersect_ray(q)
	if not hit.is_empty():
		p = hit["position"]
	_ghost.global_position = p
	_ghost.rotation.y = main.player.yaw + PI + _gyaw


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
		arr.append({"id": rec["id"], "p": [p.x, p.y, p.z], "yaw": rec["yaw"], "obsah": rec.get("obsah", {})})
	return {"inv": inv, "polozene": arr}


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
		spawn({"id": String(r["id"]), "p": Vector3(a[0], a[1], a[2]), "yaw": float(r["yaw"]), "obsah": obsah})
