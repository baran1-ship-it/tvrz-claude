extends Node
## Sber bylin a hub. Sberna mista: rostliny ve svete (kopriva, vlastovicnik, barvinek - instance z svet.gd)
## a houby v lese pod stromy (vlastni MultiMesh z modelu predmetu). Dovednost bylinkarstvi roste sberem:
## na nizke urovni jeden kus a ne vsechno pozna, s vyssi urovni vic kusu a k tomu i jiny druh rostouci vedle.
## Utrzene misto dorusta po DORUST dnech.

const DORUST := 3
const XP_UROVNE := [0, 8, 25, 55, 100]          # body bylinkarstvi pro uroven 1..5
## kdo je jak tezky poznat (uroven bylinkarstvi); do te doby "Neznama bylina/houba"
const POZNAT := {"kopriva": 1, "hriby": 1, "barvinek": 2, "bedly": 2, "vlastovicnik": 3}
const HOUBY := {"hriby": ["smrk", "dub_stary", "dub_stredni", "buk_stredni"], "bedly": ["dub", "lipa", "briza"]}
const BUNKA := 6.0

var main: Node
var spots: Array = []              # {"id", "mmi", "i", "xf"} - viz svet.gd sber_spots
var _grid := {}                    # Vector2i -> [index]
var trhano := {}                   # index -> den utrzeni
var xp := 0
var _den := -1


func setup(p_main: Node) -> void:
	main = p_main
	process_mode = Node.PROCESS_MODE_ALWAYS          # dorustani hlida jen zmenu dne
	spots = main.svet.sber_spots
	_houby()
	for i in spots.size():
		var p: Vector3 = (spots[i]["xf"] as Transform3D).origin
		var c := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
		if not _grid.has(c):
			_grid[c] = []
		_grid[c].append(i)
	print("sber: %d mist" % spots.size())


## Houby v lese: u kazdeho ~10. stromu skupinka (hriby pod smrky a duby, bedly pod listnaci a brizami).
func _houby() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var data: Dictionary = main.svet.data
	for hid: String in HOUBY:
		var ps: PackedScene = load(main.svet.MOD + "predmety/%s.glb" % hid)
		if ps == null:
			continue
		var inst := ps.instantiate()
		var meshes := inst.find_children("*", "MeshInstance3D", true, false)
		if meshes.is_empty():
			inst.free()
			continue
		var mesh: Mesh = (meshes[0] as MeshInstance3D).mesh
		inst.free()
		var xfs: Array = []
		for key: String in data["rostliny"]:
			var kind := key.substr(0, key.rfind("_"))
			if not (HOUBY[hid] as Array).has(kind):
				continue
			var k := 0
			for t: Array in data["rostliny"][key]:
				k += 1
				if k % 10 != 0:
					continue
				var a := rng.randf() * TAU
				var r := rng.randf_range(1.4, 3.0)
				var p := Vector3(t[3] + cos(a) * r, t[7] + 0.02, t[11] + sin(a) * r)
				xfs.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.8, 1.2)), p))
		# po bunkach jako rostliny (viditelne jen zblizka)
		var cells := {}
		for xf: Transform3D in xfs:
			var c := Vector2i(floori(xf.origin.x / 64.0), floori(xf.origin.z / 64.0))
			if not cells.has(c):
				cells[c] = []
			cells[c].append(xf)
		for c: Vector2i in cells:
			var list: Array = cells[c]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = mesh
			mm.instance_count = list.size()
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.visibility_range_end = 40.0
			mmi.visibility_range_end_margin = 6.0
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(mmi)
			for i in list.size():
				mm.set_instance_transform(i, list[i])
				spots.append({"id": hid, "mmi": mmi, "i": i, "xf": list[i]})


func uroven() -> int:
	var lv := 1
	for k in XP_UROVNE.size():
		if xp >= XP_UROVNE[k]:
			lv = k + 1
	return lv


func zna(id: String) -> bool:
	return uroven() >= int(POZNAT.get(id, 1))


func nazev(id: String) -> String:
	if zna(id):
		return main.predmety.name_of(id)
	return "Neznámá houba" if HOUBY.has(id) else "Neznámá bylina"


## Sberne misto pred hracem (zamerovani stredem obrazovky jako u predmetu), nebo prazdny slovnik.
func usable(cam: Camera3D) -> Dictionary:
	var eye := cam.global_position
	var fwd := -cam.global_transform.basis.z
	var pp: Vector3 = main.player.global_position
	var c0 := Vector2i(floori(pp.x / BUNKA), floori(pp.z / BUNKA))
	var best := -1
	var bs := 1e9
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			for i: int in _grid.get(c0 + Vector2i(dx, dz), []):
				if trhano.has(i):
					continue
				var p: Vector3 = (spots[i]["xf"] as Transform3D).origin + Vector3(0, 0.15, 0)
				var to := p - eye
				var dr := Vector2(to.x, to.z).length()
				if dr > 2.3 or absf(p.y - pp.y) > 1.6:          # na dosah ruky, ne z letu
					continue
				var d := to.length()
				if d > 0.6 and fwd.dot(to / d) < 0.55:
					continue
				var sc := (to - fwd * maxf(to.dot(fwd), 0.0)).length() + dr * 0.15
				if sc < bs:
					bs = sc
					best = i
	if best < 0:
		return {}
	var s: Dictionary = spots[best]
	return {"kind": "sber", "s": best, "id": s["id"], "pos": (s["xf"] as Transform3D).origin + Vector3(0, 0.3, 0)}


func label(u: Dictionary) -> String:
	return "Sebrat" if HOUBY.has(String(u["id"])) else "Utrhnout"


## Utrhnout: pocet podle urovne; od urovne 3 i jiny druh, ktery roste do 4 m.
func pick(u: Dictionary) -> void:
	var i: int = u["s"]
	var id: String = u["id"]
	var lv := uroven()
	var n: int = [1, randi_range(1, 2), randi_range(2, 3), randi_range(2, 4), randi_range(3, 5)][lv - 1]
	var znal := zna(id)
	_vzit(i)
	main.predmety.add_inv(id, n)
	var txt := "%s ×%d" % [nazev(id), n]
	var zisk := 1 if znal else 2                      # nezname se uci rychleji
	if lv >= 3 and randf() < [0.0, 0.0, 0.3, 0.5, 0.7][lv - 1]:
		var j := _soused(i, id)
		if j >= 0:
			var id2: String = spots[j]["id"]
			var n2 := randi_range(1, maxi(1, lv - 2))
			_vzit(j)
			main.predmety.add_inv(id2, n2)
			txt += ", %s ×%d" % [nazev(id2), n2]
			zisk += 1
	var lv0 := lv
	xp += zisk
	main.life.sfx("presun", -12.0, 1.3)
	main.hud.toast("Utrhl jsi: " + txt, 2.2)
	if uroven() > lv0:
		main.hud.toast("Bylinkářství: úroveň %d" % uroven(), 3.0)


func _soused(i: int, id: String) -> int:
	var p: Vector3 = (spots[i]["xf"] as Transform3D).origin
	var c0 := Vector2i(floori(p.x / BUNKA), floori(p.z / BUNKA))
	var best := -1
	var bd := 4.0
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			for j: int in _grid.get(c0 + Vector2i(dx, dz), []):
				if j == i or trhano.has(j) or String(spots[j]["id"]) == id:
					continue
				var d := p.distance_to((spots[j]["xf"] as Transform3D).origin)
				if d < bd:
					bd = d
					best = j
	return best


func _vzit(i: int) -> void:
	trhano[i] = main.day.day_n
	var s: Dictionary = spots[i]
	var mm: MultiMesh = (s["mmi"] as MultiMeshInstance3D).multimesh
	mm.set_instance_transform(int(s["i"]), Transform3D(Basis().scaled(Vector3.ZERO), (s["xf"] as Transform3D).origin))


func _process(_dt: float) -> void:
	if main == null or main.day == null or main.day.day_n == _den:
		return
	_den = main.day.day_n
	for i: int in trhano.keys():
		if _den - int(trhano[i]) >= DORUST:
			trhano.erase(i)
			var s: Dictionary = spots[i]
			((s["mmi"] as MultiMeshInstance3D).multimesh).set_instance_transform(int(s["i"]), s["xf"])


func to_save() -> Dictionary:
	return {"xp": xp, "trhano": trhano}


func from_save(d: Dictionary) -> void:
	for i: int in trhano.keys():
		if i < spots.size():
			var s: Dictionary = spots[i]
			((s["mmi"] as MultiMeshInstance3D).multimesh).set_instance_transform(int(s["i"]), s["xf"])
	trhano.clear()
	xp = int(d.get("xp", 0))
	var t: Dictionary = d.get("trhano", {})
	for k in t:
		if int(k) < spots.size():
			_vzit(int(k))
			trhano[int(k)] = int(t[k])
