extends Node3D
## Byliny u hráče: trsy trávy Havrana (trava_sada.glb), kapradí, kopřivy podle stanoviště 1393 (hra/data/stanoviste.png).
## Buňky 10 m kolem kamery do dosah_m, každá buňka = MultiMesh na druh, náhoda podle souřadnic buňky (stejné místo =
## stejná tráva). Nejvýš 3 nové buňky za snímek (žádné nárazové práce – PDF kap. 13).

var svet: Node3D
var cfg: Dictionary
var st: Image
var sj: Dictionary
var meshe := {}
var bunky := {}
var cam: Camera3D

func postav(s: Node3D, kamera: Camera3D) -> void:
	svet = s; cam = kamera
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/byliny.json"))
	sj = JSON.parse_string(FileAccess.get_file_as_string("res://data/stanoviste.json"))
	st = load("res://data/stanoviste.png").get_image()
	var sada: Node = load("res://modely/rostliny/trava_sada.glb").instantiate()
	var trava := []; var vysoka := []
	for mi in sada.find_children("*", "MeshInstance3D", true, false):
		(vysoka if "vysoka" in mi.name else trava).append(mi.mesh)
	meshe["trava"] = trava; meshe["vysoka"] = vysoka
	for d in ["kapradi_1", "kapradi_2", "kopriva_1"]:
		var n: Node = load("res://modely/rostliny/%s.glb" % d).instantiate()
		var k := "kapradi" if d.begins_with("kapradi") else "kopriva"
		if not meshe.has(k): meshe[k] = []
		meshe[k].append(n.find_children("*", "MeshInstance3D", true, false)[0].mesh)
	aktualizuj(1000)

func _trida(x: float, z: float) -> String:
	var c := int((x - float(sj["x0_hra"])) / float(sj["krok_m"])); var r := int((z - float(sj["z0_hra"])) / float(sj["krok_m"]))
	if c < 0 or r < 0 or c >= st.get_width() or r >= st.get_height(): return ""
	return sj["tridy"][int(st.get_pixel(c, r).r8)]

func _process(_d: float) -> void:
	if cam and Engine.get_process_frames() % 10 == 0:
		aktualizuj(3)

func aktualizuj(max_novych: int) -> void:
	var p := cam.global_position
	var B: float = cfg["bunka_m"]; var R: float = cfg["dosah_m"]
	var n := 0
	var chci := {}
	for i in range(floori((p.x - R) / B), floori((p.x + R) / B) + 1):
		for j in range(floori((p.z - R) / B), floori((p.z + R) / B) + 1):
			var c := Vector2((i + 0.5) * B, (j + 0.5) * B)
			if c.distance_to(Vector2(p.x, p.z)) > R + B * 0.7: continue
			var k := Vector2i(i, j); chci[k] = true
			if not bunky.has(k) and n < max_novych:
				bunky[k] = _bunka(i, j, B); n += 1
	for k in bunky.keys():
		if not chci.has(k):
			for x in bunky[k]: x.queue_free()
			bunky.erase(k)

func _bunka(i: int, j: int, B: float) -> Array:
	var rng := RandomNumberGenerator.new(); rng.seed = hash(Vector2i(i, j))
	var tridy: Dictionary = cfg["tridy"]
	var mista := {}   # druh -> [Transform3D]
	var vzorku := int(B * B * 6.0)
	for t in vzorku:
		var x := (i + rng.randf()) * B; var z := (j + rng.randf()) * B
		var tr := _trida(x, z)
		if not tridy.has(tr): continue
		var h: Dictionary = tridy[tr]
		for druh in h:
			if rng.randf() < float(h[druh]) / 6.0:
				var s := rng.randf_range(0.8, 1.3)
				var y: float = svet.vyska(x, z)
				var tf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.85, 1.2), s)), Vector3(x, y - 0.03, z))
				var klic: String = druh + str(rng.randi() % meshe[druh].size())
				if not mista.has(klic): mista[klic] = []
				mista[klic].append(tf)
	var out := []
	for klic in mista:
		var druh: String = klic.rstrip("0123456789")
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = meshe[druh][int(klic.substr(druh.length()))]
		var a: Array = mista[klic]
		mm.instance_count = a.size()
		for q in a.size(): mm.set_instance_transform(q, a[q])
		var mi := MultiMeshInstance3D.new(); mi.multimesh = mm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi); out.append(mi)
	return out
