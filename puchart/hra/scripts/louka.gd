extends Node3D
## Louka z trsů trávy (převzato z Havrana scripts/louka.gd, Míša 4. 11.: „na louce není tráva jen rastr“): buňky
## bunka_m kolem kamery, rozsev po krok_m s náhodou podle souřadnic (stejné místo = stejná tráva) ve vlákně, hustota
## podle stanoviště 1393 (data/louka.json tridy). Trs = 3 zkřížené karty z atlasu, MultiMesh s jednotkovou transformací,
## pata a druh v INSTANCE_CUSTOM (stebla.gdshader z_custom) – shader trs zmenší k patě, když hash > hustota(vzdálenost).

var svet: Node3D
var cam: Camera3D
var cfg: Dictionary
var sj: Dictionary
var st: Image
var _trs: Mesh
var bunky := {}            # Vector2i -> MultiMeshInstance3D / null (prázdná)
var _ceka := {}            # Vector2i -> id úlohy
var _hotove: Array = []
var _zamek := Mutex.new()
const ATLAS_POMER := 341.0 / 256.0   # Havran: šířka : výška buňky atlasu (3×2, 1024×512)

func postav(s: Node3D, kamera: Camera3D) -> void:
	svet = s; cam = kamera
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/louka.json"))
	sj = JSON.parse_string(FileAccess.get_file_as_string("res://data/stanoviste.json"))
	st = load("res://data/stanoviste.png").get_image()
	_trs = _karta_mesh(3, ATLAS_POMER, 1.0)
	var m := _trs.surface_get_material(0) as ShaderMaterial
	m.set_shader_parameter("z_custom", true)
	m.set_shader_parameter("hust_od", float(cfg["hust_od_m"])); m.set_shader_parameter("hust_do", float(cfg["hust_do_m"]))
	m.set_shader_parameter("hust_konec", float(cfg["hust_do_m"]))

	if str(cfg.get("rezim", "bunky")) == "mrizka": _mrizka_postav()

## ---- MŘÍŽKA kolem kamery (louka.json mrizka; stebla.gdshader mrizka) – žádný rozsev na CPU ani vlákna
var _prst: Array = []   # [MultiMeshInstance3D, krok]
func _mrizka_postav() -> void:
	set_process(true)
	var M: Dictionary = cfg["mrizka"]
	var vi: Dictionary = svet.vinfo; var w := int(vi["sirka"]); var hh := int(vi["vyska"])
	var hi: PackedByteArray = svet.sit_hi if not svet.sit_hi.is_empty() else svet.vys_hi
	var lo: PackedByteArray = svet.sit_lo if not svet.sit_lo.is_empty() else svet.vys_lo
	var t_hi := ImageTexture.create_from_image(Image.create_from_data(w, hh, false, Image.FORMAT_L8, hi))
	var t_lo := ImageTexture.create_from_image(Image.create_from_data(w, hh, false, Image.FORMAT_L8, lo))
	var sti := st.duplicate(); if sti.is_compressed(): sti.decompress()
	sti.convert(Image.FORMAT_L8); var t_st := ImageTexture.create_from_image(sti)
	# tabulka tříd 256 × 2: řádek 0 = (hustota, kumulativně druh 0, 1, 2), řádek 1 = (kumulativně druh 3)
	var tb := Image.create(256, 2, false, Image.FORMAT_RGBA8)
	var tridy: Dictionary = cfg["tridy"]; var druhy: Dictionary = cfg["druhy"]
	for i in sj["tridy"].size():
		var jm: String = sj["tridy"][i]; var pod: Array = druhy.get(jm, druhy["_"])
		var c := [0.0, 0.0, 0.0, 0.0]; var acc := 0.0
		for k in 4: acc += float(pod[k]); c[k] = acc
		tb.set_pixel(i, 0, Color(minf(float(tridy.get(jm, 0.0)), 1.0), c[0], c[1], c[2])); tb.set_pixel(i, 1, Color(c[3], 1.0 if jm.begins_with("les") or jm == "luh" else 0.0, 0, 0))
	var t_tb := ImageTexture.create_from_image(tb)
	var kri: Image = load("res://data/kryt.png").get_image() if ResourceLoader.exists("res://data/kryt.png") else Image.create(4, 4, false, Image.FORMAT_L8)
	if kri.is_compressed(): kri.decompress()
	kri.convert(Image.FORMAT_L8); var t_kr := ImageTexture.create_from_image(kri)
	var LS: Dictionary = cfg.get("les", {})
	var pr: Array = M["prstence"]; var karty: Array = M.get("karty", [3, 3, 3]); var vnitr := 0.0
	for ri in pr.size():
		var krok := float(pr[ri][0]); var do_ := float(pr[ri][1])
		var mesh := _karta_mesh(int(karty[ri]), ATLAS_POMER, 1.0)
		var m := mesh.surface_get_material(0) as ShaderMaterial
		m.set_shader_parameter("mrizka", true)
		for kv in [["vys_hi", t_hi], ["vys_lo", t_lo], ["stan", t_st], ["tab", t_tb], ["kryt", t_kr]]: m.set_shader_parameter(kv[0], kv[1])
		m.set_shader_parameter("les_kryt", Vector4(float(LS.get("kryt_od", 0.6)), float(LS.get("kryt_do", 1.0)), float(LS.get("ubytek", 0.9)), float(LS.get("dosah_m", 18.0))))
		var pas := float(M.get("prolnuti_m", 3.0))
		m.set_shader_parameter("r_od", vnitr if ri > 0 else -1.0); m.set_shader_parameter("r_do", do_); m.set_shader_parameter("r_pas", pas)
		m.set_shader_parameter("vys_info", Vector4(float(vi["x0_hra"]), float(vi["z0_hra"]), w, hh))
		m.set_shader_parameter("vys_h0", 300.0 - float(vi["pocatek_H"]))
		m.set_shader_parameter("stan_info", Vector4(float(sj["x0_hra"]), float(sj["z0_hra"]), float(sj["krok_m"]), st.get_width()))
		m.set_shader_parameter("krok_m", krok)
		m.set_shader_parameter("hust_od", float(cfg["hust_od_m"])); m.set_shader_parameter("hust_do", float(cfg["hust_do_m"]))
		m.set_shader_parameter("hust_konec", float(cfg["hust_do_m"]))
		var n := int(ceil(do_ / krok)); var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_custom_data = true; mm.mesh = mesh
		var body := []
		for j in range(-n, n + 1):
			for i in range(-n, n + 1):
				var o := Vector2(i * krok, j * krok)
				if o.length() > do_ + krok: continue
				if ri > 0 and o.length() < vnitr - float(M.get("prolnuti_m", 3.0)) - krok: continue   # vnitřek kreslí jemnější prstenec (pás prolnutí kreslí oba)
				body.append(o)
		mm.instance_count = body.size()
		for k in body.size():
			mm.set_instance_transform(k, Transform3D.IDENTITY)
			mm.set_instance_custom_data(k, Color(body[k].x, body[k].y, 0, 0))
		mm.custom_aabb = AABB(Vector3(-do_ - 2, -300, -do_ - 2), Vector3(2 * do_ + 4, 600, 2 * do_ + 4))
		var mi := MultiMeshInstance3D.new(); mi.multimesh = mm; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi); _prst.append([mi, krok])
		print("LOUKA mřížka prstenec krok %.1f m do %.0f m: %d trsů" % [krok, do_, body.size()])
		vnitr = do_

func _mrizka_tick() -> void:
	var p := cam.global_position
	for q in _prst:
		var k: float = q[1]
		(q[0] as Node3D).global_position = Vector3(roundf(p.x / k) * k, 0.0, roundf(p.z / k) * k)

func vsechny_site() -> Array: return [_trs] + _prst.map(func(q): return (q[0] as MultiMeshInstance3D).multimesh.mesh)

func _trida(x: float, z: float) -> String:
	var c := int((x - float(sj["x0_hra"])) / float(sj["krok_m"])); var r := int((z - float(sj["z0_hra"])) / float(sj["krok_m"]))
	if c < 0 or r < 0 or c >= st.get_width() or r >= st.get_height(): return ""
	return sj["tridy"][int(st.get_pixel(c, r).r8)]

func _process(_d: float) -> void:
	if cam == null or _trs == null: return
	if not _prst.is_empty(): _mrizka_tick(); return
	var B := float(cfg["bunka_m"]); var R := float(cfg["dosah_m"]); var p := cam.global_position
	var c0 := Vector2i(int(floor(p.x / B)), int(floor(p.z / B))); var n := int(ceil(R / B))
	var nove := 0
	for i in range(-n, n + 1):
		for j in range(-n, n + 1):
			var k := c0 + Vector2i(i, j)
			if bunky.has(k) or _ceka.has(k): continue
			var stred := Vector2((k.x + 0.5) * B, (k.y + 0.5) * B)
			if stred.distance_to(Vector2(p.x, p.z)) > R + B * 0.71: continue
			if nove >= int(cfg["nove_za_snimek"]) * 2: continue
			_ceka[k] = WorkerThreadPool.add_task(_rozsej.bind(k)); nove += 1
	_zamek.lock(); var hot := _hotove.duplicate(); _hotove.clear(); _zamek.unlock()
	for h in hot: _vloz(h)
	for k in bunky.keys():   # uvolnit vzdálené
		var stred := Vector2((k.x + 0.5) * B, (k.y + 0.5) * B)
		if stred.distance_to(Vector2(p.x, p.z)) > R + B * 1.6:
			if bunky[k] != null: bunky[k].queue_free()
			bunky.erase(k)

func _rozsej(k: Vector2i) -> void:
	var B := float(cfg["bunka_m"]); var krok := float(cfg["krok_m"])
	var rng := RandomNumberGenerator.new(); rng.seed = hash(Vector2i(k.x * 7919, k.y * 104729))
	var tridy: Dictionary = cfg["tridy"]; var druhy: Dictionary = cfg["druhy"]
	var cust := PackedFloat32Array(); var x0 := k.x * B; var z0 := k.y * B
	var cx := x0 + B * 0.5; var cz := z0 + B * 0.5
	var z := 0.0
	while z < B:
		var x := 0.0
		while x < B:
			var px := x0 + x + rng.randf_range(-0.45, 0.45) * krok; var pz := z0 + z + rng.randf_range(-0.45, 0.45) * krok
			var tr := _trida(px, pz); var h := float(tridy.get(tr, 0.0))
			if h > 0.0 and rng.randf() < h:
				var pod: Array = druhy.get(tr, druhy["_"]); var u := rng.randf(); var druh := 0; var acc := 0.0
				for di in pod.size():
					acc += float(pod[di])
					if u <= acc: druh = di; break
				var hs := rng.randf() * 0.999
				cust.append_array([float(druh) + hs, px - cx, svet.vyska(px, pz) - 0.04, pz - cz])
			x += krok
		z += krok
	_zamek.lock(); _hotove.append([k, cust]); _zamek.unlock()

func _vloz(h: Array) -> void:
	var k: Vector2i = h[0]; var cust: PackedFloat32Array = h[1]
	if _ceka.has(k): WorkerThreadPool.wait_for_task_completion(_ceka[k]); _ceka.erase(k)
	var n := cust.size() / 4
	if n == 0: bunky[k] = null; return
	var B := float(cfg["bunka_m"])
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_custom_data = true; mm.mesh = _trs
	mm.instance_count = n
	for i in n:
		mm.set_instance_transform(i, Transform3D.IDENTITY)
		mm.set_instance_custom_data(i, Color(cust[4 * i], cust[4 * i + 1], cust[4 * i + 2], cust[4 * i + 3]))
	mm.custom_aabb = AABB(Vector3(-B * 0.5 - 1, -200, -B * 0.5 - 1), Vector3(B + 2, 400, B + 2))
	var mi := MultiMeshInstance3D.new(); mi.multimesh = mm; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.position = Vector3((k.x + 0.5) * B, 0, (k.y + 0.5) * B)
	add_child(mi); bunky[k] = mi

func _karta_mesh(n: int, sirka: float, vyska: float) -> Mesh:   # Havran louka.gd _karta_mesh (bez karty shora)
	var stt := SurfaceTool.new(); stt.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hw := 0.5 * sirka
	var posun := [Vector3(0.0, 0, 0.0), Vector3(0.09, 0, -0.06), Vector3(-0.07, 0, 0.08), Vector3(0.05, 0, 0.1)]
	var vysky := [1.0, 0.86, 0.93, 0.8]
	for q in n:
		var ang := PI * q / n + 0.35
		var tg := Vector3(cos(ang), 0, sin(ang)) * hw
		var nrm := Vector3(-sin(ang), 0, cos(ang))
		var stred: Vector3 = posun[q % 4] * sirka
		var up := Vector3(0, vyska * float(vysky[q % 4]), 0)
		var pts := [stred - tg, stred + tg, stred + tg + up, stred - tg + up]
		var u0 := 1.0 if q == 1 else 0.0
		var uvs := [Vector2(u0, 1), Vector2(1.0 - u0, 1), Vector2(1.0 - u0, 0), Vector2(u0, 0)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			stt.set_uv(uvs[i]); stt.set_normal(nrm); stt.add_vertex(pts[i])
	var mesh := stt.commit()
	var mat := ShaderMaterial.new(); mat.shader = load("res://shaders/stebla.gdshader")
	mat.set_shader_parameter("atlas", load("res://textury/trava_atlas.png")); mat.set_shader_parameter("vitr", 1.0)
	mesh.surface_set_material(0, mat)
	return mesh

func _exit_tree() -> void:   # vlákna dokončit před zrušením uzlu
	for k in _ceka: WorkerThreadPool.wait_for_task_completion(_ceka[k])
	_ceka.clear()
