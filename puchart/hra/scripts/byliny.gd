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
	if ResourceLoader.exists("res://data/kamenitost.png"): km_img = load("res://data/kamenitost.png").get_image()   # kde je kamenito (stavby_vegetace.py)
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
			n.queue_free()   # ne free(): okamžité uvolnění 3D uzlu během načítání shodilo hru na tabletu (renderer_scene_cull, 11. 11.)
	# pás u paty plotů a zdí (stavby_vegetace.py → data/pata_pas.json, byliny.json pata_pas; Míša 13. 11., KCD předloha vsi)
	if cfg.has("pata_pas") and FileAccess.file_exists("res://data/pata_pas.json"):
		var pp: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/pata_pas.json"))
		if pp is Dictionary and is_equal_approx(float(pp.get("bunka_m", 0.0)), float(cfg["bunka_m"])): _pas = pp["bunky"]
	# uvnitř staveb vsi nic neroste (Míša 13. 11.: „v hájovně je tráva“) – půdorysy z mista_stavby.json, zúžené o okraj na líc zdi
	if FileAccess.file_exists("res://data/mista_stavby.json"):
		var ms: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/mista_stavby.json"))
		for q: Array in ms.get("pudorysy", []):
			var pg := PackedVector2Array()
			for v: Array in q: pg.append(Vector2(float(v[0]), float(v[1])))
			var zuz := Geometry2D.offset_polygon(pg, -float(cfg.get("stavba_okraj_m", 0.3)))
			if zuz.is_empty(): continue
			var pz: PackedVector2Array = zuz[0]; var bb := Rect2(pz[0], Vector2.ZERO)
			for v in pz: bb = bb.expand(v)
			_stavby.append([bb, pz])
	aktualizuj(1000)

var _pas := {}   # "i,j" -> skvrny [x0, z0, x1, z1, nx, nz, šířka, zdroj]

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
var _stavby: Array = []   # [Rect2, polygon] líců zdí staveb vsi

func _ve_stavbe(x: float, z: float) -> bool:
	var p := Vector2(x, z)
	for e: Array in _stavby:
		if (e[0] as Rect2).has_point(p) and Geometry2D.is_point_in_polygon(p, e[1]): return true
	return false

func _pocitej(i: int, j: int, B: float) -> Dictionary:
	var out := {}
	for tf: Array in _bunka_mista(i, j, B):
		var klic: String = tf[0]; var t: Transform3D = tf[1]
		if not _stavby.is_empty() and _ve_stavbe(t.origin.x, t.origin.z): continue
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

var km_img: Image = null
func _kamenitost(x: float, z: float) -> float:
	var c := clampi(int((x - float(sj["x0_hra"])) / float(sj["krok_m"])), 0, km_img.get_width() - 1)
	var r := clampi(int((z - float(sj["z0_hra"])) / float(sj["krok_m"])), 0, km_img.get_height() - 1)
	return km_img.get_pixel(c, r).r

## (vlákno) ležící kmen: osa X modelu leží na zemi mezi konci (délka z AABB modelu × měřítko, sklon z výšek konců);
## konce, střed a čtvrtiny ne na zakázané třídě; třída v les_okoli jen s lesem a bez zakázané třídy do r m; strmý svah nebo hrbol = null
func _lezici(x: float, z: float, s: float, yaw: float, nv: float, m: Mesh, lz: Dictionary, tr: String) -> Variant:
	var L: float = maxf(absf(m.get_aabb().position.x), absf(m.get_aabb().end.x)) * s
	var d := Basis(Vector3.UP, yaw).x
	var a := Vector2(x - d.x * L, z - d.z * L); var b := Vector2(x + d.x * L, z + d.z * L)
	var zak: Array = lz.get("zakazane_tridy", [])
	for f in [0.0, 0.25, 0.5, 0.75, 1.0]:
		var p := a.lerp(b, f); var t := _trida(p.x, p.y)
		if t == "" or t in zak: return null
	var lo: Dictionary = lz.get("les_okoli", {})
	if lo.has(tr):
		var r := float(lo[tr]); var les := false
		for u in 8:
			var t := _trida(x + r * cos(u * PI / 4), z + r * sin(u * PI / 4))
			if t in zak: return null   # louka, ves, cesta do r m: ne
			if t.begins_with("les_") or t in lz.get("les_tridy", []): les = true
		if not les: return null
	var ha: float = svet.vyska(a.x, a.y); var hb: float = svet.vyska(b.x, b.y)
	var sk := atan2(hb - ha, 2.0 * L)
	if absf(rad_to_deg(sk)) > float(lz.get("max_sklon_st", 25.0)): return null
	for f in [0.25, 0.5, 0.75]:   # hrbol pod kmenem: konce by visely
		var p := a.lerp(b, f)
		if svet.vyska(p.x, p.y) > lerpf(ha, hb, f) + float(lz.get("max_hrbol_m", 0.35)): return null
	var vn: Array = lz.get("vyska_nahoda", [1.0, 1.0])
	var bz := Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, sk) * Basis.from_scale(Vector3(s, s * lerpf(float(vn[0]), float(vn[1]), nv), s))
	return Transform3D(bz, Vector3(x, (ha + hb) * 0.5 - float(cfg.get("pata_zapusteni_m", 0.03)), z))

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
			var nk := 1.0
			if km_img != null and druh in cfg.get("podle_kamenitosti", {}).get("druhy", []):   # úlomky podle svahu, zdí a pruhů, ne všude stejně
				var pk: Dictionary = cfg["podle_kamenitosti"]   # u hradů přidává, v lese jen přeskupuje (průměr ×0,95 – rozpočet scén)
				var nas_k: float = float(pk["nasobek"]) if tr in pk.get("tridy", []) else float(pk.get("les", {}).get("nasobek", 1.0))
				nk = _kamenitost(x, z) * nas_k
			if rng.randf() < float(h[druh]) * nas * nk / na_m2:
				var mr: Array = cfg.get("meritko_druh", {}).get(druh, cfg.get("meritko", [0.8, 1.3]))
				var s := rng.randf_range(float(mr[0]), float(mr[1]))
				var lz: Dictionary = cfg.get("lezi", {}).get(druh, {})
				if not lz.is_empty():   # ležící kmen (byliny.json lezi; Míša 13. 11.: padlé stromy, ne na cestě, u vody jen v lese)
					var iv: int = rng.randi() % (meshe[druh] as Array).size()
					var tl: Variant = _lezici(x, z, s, rng.randf() * TAU, rng.randf(), meshe[druh][iv], lz, tr)
					if tl == null: continue
					if not mista.has(druh + str(iv)): mista[druh + str(iv)] = []
					mista[druh + str(iv)].append(tl)
					continue
				var y: float = svet.vyska(x, z)
				var rp: float = float(cfg.get("pata_polomer_m", {}).get(druh, cfg.get("pata_polomer_m", {}).get("_", 0.25))) * s
				for u in 4:   # na svahu sednout na nejnižší bod obvodu paty (Míša 3. 11.: nic nelevituje)
					y = minf(y, svet.vyska(x + rp * cos(u * PI / 2 + 0.785), z + rp * sin(u * PI / 2 + 0.785)))
				var tf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.85, 1.2), s)), Vector3(x, y - float(cfg.get("pata_zapusteni_m", 0.03)), z))
				var klic: String = druh + str(rng.randi() % meshe[druh].size())
				if not mista.has(klic): mista[klic] = []
				mista[klic].append(tf)
	# pás u paty: trsy podél hrany, u zdi hustěji (vzdálenost = šířka × náhoda^1,6)
	var kp := "%d,%d" % [i, j]
	if _pas.has(kp):
		for sk: Array in _pas[kp]:
			# čára vody (stavby_vegetace.py voda_pas, Míša 13. 11.): hustoty voda_pas[zdroj], trsy nakloněné k vodě, část přes čáru
			var voda: bool = sk.size() > 9
			if voda and not cfg.has("voda_pas"): continue
			var hp: Dictionary = cfg["voda_pas"].get(str(sk[7]), {}) if voda else cfg["pata_pas"]
			var a := Vector2(float(sk[0]), float(sk[1])); var b := Vector2(float(sk[2]), float(sk[3])); var nn := Vector2(float(sk[4]), float(sk[5])); var w := float(sk[6])
			var plocha := a.distance_to(b) * w
			var osa := Vector3(b.x - a.x, 0.0, b.y - a.y).normalized()
			var k_vode := 1.0 if Vector3(-osa.z, 0.0, osa.x).dot(Vector3(-nn.x, 0.0, -nn.y)) > 0.0 else -1.0   # znaménko otočení vrcholu k vodě
			for druh: String in hp:
				if not (hp[druh] is float or hp[druh] is int) or not meshe.has(druh) or meshe[druh].is_empty(): continue
				var n := int(plocha * float(hp[druh]) + rng.randf())
				for q in n:
					var p := a.lerp(b, rng.randf()) + nn * (w * pow(rng.randf(), 1.6))
					if voda: p -= nn * float(sk[9]) * rng.randf() * rng.randf()   # přes čáru vody (převis, 0–presah_m)
					var mr: Array = cfg.get("meritko_druh", {}).get(druh, cfg.get("meritko", [0.8, 1.3]))
					var sc := rng.randf_range(float(mr[0]), float(mr[1]))
					var y: float = svet.vyska(p.x, p.y)
					var rp: float = float(cfg.get("pata_polomer_m", {}).get(druh, cfg.get("pata_polomer_m", {}).get("_", 0.25))) * sc
					for u in 4: y = minf(y, svet.vyska(p.x + rp * cos(u * PI / 2 + 0.785), p.y + rp * sin(u * PI / 2 + 0.785)))
					var bz := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, sc * rng.randf_range(0.85, 1.2), sc))
					if voda: bz = Basis(osa, k_vode * deg_to_rad(float(sk[8])) * rng.randf_range(0.5, 1.2)) * bz   # nakloněný k vodě (30–50°)
					var tf := Transform3D(bz, Vector3(p.x, y - float(cfg.get("pata_zapusteni_m", 0.03)), p.y))
					var klic: String = druh + str(rng.randi() % meshe[druh].size())
					if not mista.has(klic): mista[klic] = []
					mista[klic].append(tf)
	var vys := []
	for klic in mista:
		for t in mista[klic]: vys.append([klic, t])
	return vys

func _exit_tree() -> void:   # vlákna dokončit před zrušením uzlu (hlídač skriptů 4. 11.: _mutex null při ukončení)
	for k in _ve_vlakne: WorkerThreadPool.wait_for_task_completion(_ve_vlakne[k])
	_ve_vlakne.clear()
