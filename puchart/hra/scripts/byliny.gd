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
var _sum := FastNoiseLite.new()

func postav(s: Node3D, kamera: Camera3D, cesta := "res://data/byliny.json") -> void:
	svet = s; cam = kamera
	cfg = JSON.parse_string(FileAccess.get_file_as_string(cesta))
	sj = JSON.parse_string(FileAccess.get_file_as_string("res://data/stanoviste.json"))
	st = load("res://data/stanoviste.png").get_image()
	if cfg.get("trava_sada", true) and ResourceLoader.exists("res://modely/rostliny/trava_sada.glb"):
		var sada: Node = load("res://modely/rostliny/trava_sada.glb").instantiate()
		var trava := []; var vysoka := []
		for mi in sada.find_children("*", "MeshInstance3D", true, false):
			(vysoka if "vysoka" in mi.name else trava).append(mi.mesh)
		var zk: Array = cfg.get("zanik_m", [])
		if zk.size() == 2:
			trava = trava.map(func(x: Mesh) -> Mesh: return _fade(x, float(zk[0]), float(zk[1])))
			vysoka = vysoka.map(func(x: Mesh) -> Mesh: return _fade(x, float(zk[0]), float(zk[1])))
		meshe["trava"] = trava; meshe["vysoka"] = vysoka
	var modely: Dictionary = cfg.get("modely", {})
	var zanik: Array = cfg.get("zanik_m", [])
	for k in modely:   # druh -> modely (tabulka modely); se zanik_m rozpouštění ditheringem do dálky (žádné odskočení)
		meshe[k] = []
		for d in modely[k]:
			if not ResourceLoader.exists("res://modely/rostliny/%s.glb" % d): continue
			var n: Node = load("res://modely/rostliny/%s.glb" % d).instantiate()
			for mi in n.find_children("*", "MeshInstance3D", true, false):
				var m: Mesh = (mi as MeshInstance3D).mesh
				if zanik.size() == 2: m = _fade(m, float(zanik[0]), float(zanik[1]))
				meshe[k].append(m)
			n.free()
	aktualizuj(1000)

var _listi_sh: Shader
func _fade(m: Mesh, od: float, do_: float) -> Mesh:
	var mm: Mesh = m.duplicate(); var bb := m.get_aabb()
	for i in mm.get_surface_count():
		var mat := mm.surface_get_material(i)
		if cfg.get("listi", false) and mat is BaseMaterial3D and (mat as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED and (mat as BaseMaterial3D).albedo_texture:
			# keře: listí jako stromy (Havran listi.gdshader: normály od středu, vítr, prosvítání) + rozpouštění do dálky
			if _listi_sh == null: _listi_sh = load("res://shaders/listi.gdshader")
			var sm := ShaderMaterial.new(); sm.shader = _listi_sh
			sm.set_shader_parameter("barva", (mat as BaseMaterial3D).albedo_texture); sm.set_shader_parameter("tint", (mat as BaseMaterial3D).albedo_color)
			sm.set_shader_parameter("prah", maxf((mat as BaseMaterial3D).alpha_scissor_threshold, 0.3))
			sm.set_shader_parameter("stred", Vector3(bb.get_center().x, bb.position.y + bb.size.y * 0.5, bb.get_center().z))
			sm.set_shader_parameter("vyska", maxf(bb.end.y, 0.5)); sm.set_shader_parameter("sila_vetru", 0.6); sm.set_shader_parameter("objem", 0.5)
			sm.set_shader_parameter("zanik", Vector2(do_, od))
			mm.surface_set_material(i, sm); continue
		if mat is BaseMaterial3D:
			var c: BaseMaterial3D = mat.duplicate()
			c.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_DITHER
			c.distance_fade_min_distance = do_; c.distance_fade_max_distance = od   # min > max = mizí s dálkou
			mm.surface_set_material(i, c)
	return mm

func vsechny_site() -> Array:
	var a := []
	for k in meshe: a.append_array(meshe[k])
	return a

func _trida(x: float, z: float) -> String:
	var c := int((x - float(sj["x0_hra"])) / float(sj["krok_m"])); var r := int((z - float(sj["z0_hra"])) / float(sj["krok_m"]))
	if c < 0 or r < 0 or c >= st.get_width() or r >= st.get_height(): return ""
	return sj["tridy"][int(st.get_pixel(c, r).r8)]

func _process(_d: float) -> void:
	var nb: Dictionary = cfg.get("nove_bunky", {"kazdych_snimku": 10, "pocet": 3})   # byliny.json (2. 11.: nárazová práce = zásek)
	if cam and Engine.get_process_frames() % int(nb["kazdych_snimku"]) == 0:
		aktualizuj(int(nb["pocet"]))

## Havran louka.gd (0.64, sekání): buňky se počítají ve vlákně (WorkerThreadPool) a vznikají PŘEDEM – do dosah_m +
## predstih_m, viditelné jen do dosah_m (rozpouštění zanik_m), takže tráva nevyroste před očima (Míša 3. 11.: „nejdřív
## je povrch a pak vyrostou trsy“). Hlavní vlákno jen vloží hotový buffer (MultiMesh.buffer), nejvýš vlozit_za_snimek.
var _ve_vlakne := {}     # klíč buňky -> id úlohy
var _hotove := {}        # klíč buňky -> {klic: PackedFloat32Array}
var _mutex := Mutex.new()

func aktualizuj(max_novych: int) -> void:
	var p := cam.global_position
	var B: float = cfg["bunka_m"]; var R: float = float(cfg["dosah_m"]) + float(cfg.get("predstih_m", 0.0))
	var chci := {}; var nove: Array = []
	for i in range(floori((p.x - R) / B), floori((p.x + R) / B) + 1):
		for j in range(floori((p.z - R) / B), floori((p.z + R) / B) + 1):
			var c := Vector2((i + 0.5) * B, (j + 0.5) * B)
			var dd := c.distance_to(Vector2(p.x, p.z))
			if dd > R + B * 0.7: continue
			var k := Vector2i(i, j); chci[k] = true
			if not bunky.has(k) and not _ve_vlakne.has(k): nove.append([dd, k])
	nove.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))   # nejbližší první
	var n := 0
	for e in nove:
		if n >= max_novych: break
		var k: Vector2i = e[1]
		if max_novych >= 1000:   # start: hned (za načítací obrazovkou)
			bunky[k] = _vloz(_pocitej(k.x, k.y, B))
		else:
			_ve_vlakne[k] = WorkerThreadPool.add_task(_uloha.bind(k, B), false, "byliny")
		n += 1
	# hotové z vlákna vložit (nejvýš vlozit_za_snimek buněk za snímek)
	var vl := 0
	for k in _ve_vlakne.keys():
		if vl >= int(cfg.get("vlozit_za_snimek", 1)): break
		if WorkerThreadPool.is_task_completed(_ve_vlakne[k]):
			WorkerThreadPool.wait_for_task_completion(_ve_vlakne[k]); _ve_vlakne.erase(k)
			_mutex.lock(); var data: Dictionary = _hotove.get(k, {}); _hotove.erase(k); _mutex.unlock()
			if chci.has(k): bunky[k] = _vloz(data); vl += 1
	for k in bunky.keys():
		if not chci.has(k):
			for x in bunky[k]: x.queue_free()
			bunky.erase(k)

func _uloha(k: Vector2i, B: float) -> void:
	var d := _pocitej(k.x, k.y, B)
	_mutex.lock(); _hotove[k] = d; _mutex.unlock()

## (vlákno) polohy trsů buňky -> {klic druh+varianta: PackedFloat32Array 12 čísel na trs}
func _pocitej(i: int, j: int, B: float) -> Dictionary:
	var out := {}
	for tf: Array in _bunka_mista(i, j, B):
		var klic: String = tf[0]; var t: Transform3D = tf[1]
		if not out.has(klic): out[klic] = PackedFloat32Array()
		var bs := t.basis; var o := t.origin
		out[klic].append_array(PackedFloat32Array([bs.x.x, bs.y.x, bs.z.x, o.x - (i + 0.5) * B, bs.x.y, bs.y.y, bs.z.y, o.y, bs.x.z, bs.y.z, bs.z.z, o.z - (j + 0.5) * B]))
	out["_stred"] = Vector3((i + 0.5) * B, 0.0, (j + 0.5) * B)   # uzel buňky ve středu: visibility_range měří od polohy uzlu
	return out

## (hlavní vlákno) MultiMesh z hotového bufferu
func _vloz(data: Dictionary) -> Array:
	var vys := []
	for klic: String in data:
		if klic == "_stred": continue
		var druh: String = klic.rstrip("0123456789")
		var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = meshe[druh][int(klic.substr(druh.length()))]
		var buf: PackedFloat32Array = data[klic]
		mm.instance_count = buf.size() / 12; mm.buffer = buf
		var mi := MultiMeshInstance3D.new(); mi.multimesh = mm
		mi.position = data.get("_stred", Vector3.ZERO)
		mi.visibility_range_end = float(cfg["dosah_m"]) + float(cfg["bunka_m"]) * 0.75   # buňky předstihu se nekreslí (jen připravené)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if cfg.get("stin", false) else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi); vys.append(mi)
	return vys

func _bunka_mista(i: int, j: int, B: float) -> Array:
	var rng := RandomNumberGenerator.new(); rng.seed = hash(Vector2i(i, j))
	var tridy: Dictionary = cfg["tridy"]
	var mista := {}   # druh -> [Transform3D]
	var na_m2 := float(cfg.get("vzorku_na_m2", 6.0))
	var sh: Dictionary = cfg.get("shluky", {})
	var vzorku := int(B * B * na_m2)
	for t in vzorku:
		var x := (i + rng.randf()) * B; var z := (j + rng.randf()) * B
		var tr := _trida(x, z)
		if not tridy.has(tr): continue
		var h: Dictionary = tridy[tr]
		var nas := 1.0
		if not sh.is_empty():   # shluky: hustota × šum (světliny a hustá místa, ne rovnoměrný posyp)
			nas = lerpf(float(sh["min"]), float(sh["max"]), clampf(_sum.get_noise_2d(x / float(sh["vlna_m"]), z / float(sh["vlna_m"])) * 0.5 + 0.5, 0.0, 1.0))
		for druh in h:
			if not meshe.has(druh) or meshe[druh].is_empty(): continue
			if rng.randf() < float(h[druh]) * nas / na_m2:
				var mr: Array = cfg.get("meritko_druh", {}).get(druh, cfg.get("meritko", [0.8, 1.3]))
				var s := rng.randf_range(float(mr[0]), float(mr[1]))
				var y: float = svet.vyska(x, z)
				var tf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.85, 1.2), s)), Vector3(x, y - 0.03, z))
				var klic: String = druh + str(rng.randi() % meshe[druh].size())
				if not mista.has(klic): mista[klic] = []
				mista[klic].append(tf)
	var vys := []
	for klic in mista:
		for t in mista[klic]: vys.append([klic, t])
	return vys
