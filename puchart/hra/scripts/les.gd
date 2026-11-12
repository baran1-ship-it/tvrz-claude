extends Node3D
## Les 1393: stromy z hra/data/stromy.bin (polohy a výšky ze skutečných korun DMP 1G − DMR 5G, druh podle
## historie_vegetace.json – nastroje/stanoviste_realne.py). Modely Havrana (stromy_modely.json).
## Blízko: plné modely v buňkách (MultiMesh na buňku a variantu, auto-LOD importu podle vzdálenosti buňky).
## Dál: zkřížené karty *_daleko (6 troj.) v jednom MultiMesh na variantu.
## Přechod per pixel ditheringem podle vzdálenosti (StandardMaterial distance_fade) – strom se nekreslí dvakrát
## a nic nebliká (Compatibility nemá průhledný fade visibility range – PDF kap. 9).

var svet: Node3D
var cfg: Dictionary

var _kmeny := {}  # buňka KB m -> [Vector4(x, y, z, poloměr kmene)] – kolize kmenů kolem hráče (matice: strom|hrac, strom|kolize)
const KB := 16.0
var _kol := {}    # buňka -> StaticBody3D
var _kol_cas := 0.0
var _kr: Dictionary = {}
var _hust := {}   # buňka HB m -> počet stromů (zápoj pro mlhu v lese, prostredi.json atmosfera.les_mlha)
var HB := 16.0

## 0..1: jak hustý les je kolem bodu (3×3 buňky; od..plny stromů na buňku z prostredi.json)
func zapoj(x: float, z: float, lm: Dictionary) -> float:
	var c := Vector2i(floori(x / HB), floori(z / HB)); var n := 0
	for i in range(-1, 2):
		for j in range(-1, 2): n += _hust.get(c + Vector2i(i, j), 0)
	var od := float(lm["stromu_na_bunku_od"]); var pl := float(lm["stromu_na_bunku_plny"])
	return clampf((n / 9.0 - od) / (pl - od), 0.0, 1.0)

func postav(s: Node3D) -> void:
	svet = s
	if FileAccess.file_exists("res://data/prostredi.json"):
		HB = float(JSON.parse_string(FileAccess.get_file_as_string("res://data/prostredi.json")).get("atmosfera", {}).get("les_mlha", {}).get("bunka_m", HB))
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/stromy_modely.json"))
	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/stromy.json"))
	var raw := FileAccess.get_file_as_bytes("res://data/stromy.bin").to_float32_array()
	var dreviny: Array = info["dreviny"]
	var bl: float = cfg["blizko_m"]; var pr: float = cfg["prechod_m"]; var B: float = cfg["bunka_m"]
	var l0: float = cfg["lod0_m"]
	# snímky návrhů: PUCHART_STROMY_BLIZKO=m (karty až dál – vypadají jako krabice do ~80 m; dluh: impostory, krok D)
	if OS.get_environment("PUCHART_STROMY_BLIZKO") != "":
		bl = float(OS.get_environment("PUCHART_STROMY_BLIZKO"))
	var mer: Array = cfg["meritko"]
	_kr = cfg.get("kolize_kmene", {})
	# varianta -> seznam transformací
	var skupiny := {}
	var vynech: Array = JSON.parse_string(FileAccess.get_file_as_string("res://data/hrady_bez_stromu.json"))["obdelniky"] if FileAccess.file_exists("res://data/hrady_bez_stromu.json") else []
	for i in range(0, raw.size(), 5):
		var x := raw[i]; var z := raw[i + 1]; var h := raw[i + 2]
		var ven := false
		for o in vynech:
			if x > o[0] and x < o[2] and z > o[1] and z < o[3]:
				ven = true
		if ven:
			continue
		var hc := Vector2i(floori(x / HB), floori(z / HB)); _hust[hc] = _hust.get(hc, 0) + 1
		var kc := Vector2i(floori(x / KB), floori(z / KB))
		if not _kmeny.has(kc): _kmeny[kc] = []
		_kmeny[kc].append(Vector4(x, svet.vyska(x, z), z, maxf(float(_kr.get("min_m", 0.12)), h * float(_kr.get("na_m_vysky", 0.012)))))
		var dr: String = dreviny[int(raw[i + 3])]
		var model: String = cfg["dreviny"][dr]["model"]
		var var_h: Dictionary = cfg["varianty"][model]
		var nej := ""; var nej_d := 1e9
		for v in var_h:
			if cfg.get("stare_jako_stredni", false) and String(v).begins_with("star"): continue   # starý model jen jako LOD1 = rozmazané chuchvalce zblízka (Míša 2. 11.) -> střední plný
			var d := absf(float(var_h[v]) - h)
			if d < nej_d: nej_d = d; nej = v
		var sc := clampf(h / float(var_h[nej]), mer[0], maxf(mer[1], float(cfg.get("meritko_max_stare", mer[1]))))
		var t := Transform3D(Basis(Vector3.UP, raw[i + 4]).scaled(Vector3(sc, sc * randf_range(0.95, 1.05), sc)),
			Vector3(x, _pata(x, z, h, sc), z))
		var k := "%s_%s" % [model, nej]
		if not skupiny.has(k): skupiny[k] = []
		skupiny[k].append(t)
	var imp_meta: Dictionary = {}
	if FileAccess.file_exists("res://textury/impostory/impostory.json"):
		imp_meta = JSON.parse_string(FileAccess.get_file_as_string("res://textury/impostory/impostory.json"))
	var imp := {}   # druh -> buňka -> [Color(pata x, y, z, round(měřítko*256) + otočení/2π)]
	for k in skupiny:
		var druh: String = k.split("_")[0]
		if imp_meta.has(druh) and ResourceLoader.exists("res://textury/impostory/%s_a.png" % druh):
			var V: float = imp_meta[druh]["vyska"]
			for t: Transform3D in skupiny[k]:
				var h := float(cfg["varianty"][druh][k.substr(druh.length() + 1)]) * t.basis.get_scale().y
				var rot := fposmod(atan2(t.basis.x.z, t.basis.x.x) * -1.0, TAU)
				var bc := Vector2i(floori(t.origin.x / IMP_B), floori(t.origin.z / IMP_B))
				if not imp.has(druh): imp[druh] = {}
				if not imp[druh].has(bc): imp[druh][bc] = []
				imp[druh][bc].append(Color(t.origin.x, t.origin.y, t.origin.z, round(h / V * 256.0) + rot / TAU * 0.999))
		else:
			_daleko(k, skupiny[k], bl, pr)
		_blizko(k, skupiny[k], bl, pr, B, l0)
	_impostory(imp, imp_meta, bl, pr)

## Kolize kmenů jen v buňkách kolem hráče (stromy_modely.json kolize_kmene): válec na kmen, tělo na buňku 16 m.
func _process(d: float) -> void:
	var kc := get_viewport().get_camera_3d()
	if kc:   # LOD po stromech: poloha kamery do materiálů listí, kůry a impostorů (ne global uniform – 12. 11.)
		var kp := kc.global_position
		for m: ShaderMaterial in _lod_mat: m.set_shader_parameter("kamera_hrace", kp)
	_kol_cas -= d
	if _kol_cas > 0.0 or _kr.is_empty(): return
	_kol_cas = 0.1
	var cam := get_viewport().get_camera_3d()
	if cam == null: return
	aktualizuj_kolize(cam.global_position)

var _vse := false
func aktualizuj_kolize(p: Vector3, vse := false) -> void:
	_vse = vse
	var c0 := Vector2i(floori(p.x / KB), floori(p.z / KB)); var chci := {}
	var r := int(_kr.get("bunek_kolem", 2)); var novych := 0
	for i in range(-r, r + 1):
		for j in range(-r, r + 1):
			var c := c0 + Vector2i(i, j); chci[c] = true
			if _kol.has(c) or not _kmeny.has(c) or (novych >= 1 and not _vse): continue   # 1 buňka za volání (QA: 5 těles naráz = zásek)
			novych += 1
			var t := StaticBody3D.new(); t.name = "kmeny_%d_%d" % [c.x, c.y]
			for k: Vector4 in _kmeny[c]:
				var sh := CollisionShape3D.new(); var cy := CylinderShape3D.new(); cy.radius = k.w; cy.height = float(_kr.get("vyska_m", 4.0))
				sh.shape = cy; sh.position = Vector3(k.x, k.y + cy.height / 2 - 0.3, k.z); t.add_child(sh)
			add_child(t); _kol[c] = t
	for c in _kol.keys():
		if not chci.has(c): _kol[c].queue_free(); _kol.erase(c)

## nejbližší kmen k bodu (pro test průchodu strom_kolize)
func nejblizsi_kmen(p: Vector3) -> Vector4:
	var nej := Vector4(INF, 0, 0, 0); var nd := INF
	var c0 := Vector2i(floori(p.x / KB), floori(p.z / KB))
	for i in range(-1, 2):
		for j in range(-1, 2):
			for k: Vector4 in _kmeny.get(c0 + Vector2i(i, j), []):
				var dd := Vector2(k.x - p.x, k.z - p.z).length()
				if dd < nd: nd = dd; nej = k
	return nej

const IMP_B := 256.0   # buňka impostorů (Havran: málo volání kreslení, custom data v půl přesnosti -> pozice vůči středu buňky)

## Impostory (převzato z Havrana svet.gd _impostory): jeden čtverec na strom, pohled z atlasu 8×8 podle směru ke kameře.
func _impostory(imp: Dictionary, meta: Dictionary, bl: float, pr: float) -> void:
	var quad := ArrayMesh.new()
	var a := []; a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-1, 0, 0), Vector3(1, 0, 0), Vector3(1, 2, 0), Vector3(-1, 2, 0)])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	quad.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	var n := 0
	for d: String in imp:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/impostor.gdshader"); _lod_mat.append(m)
		m.set_shader_parameter("barva", load("res://textury/impostory/%s_a.png" % d))
		m.set_shader_parameter("normaly", load("res://textury/impostory/%s_n.png" % d))
		var st: Array = meta[d]["stred"]
		m.set_shader_parameter("stred", Vector3(st[0], st[1], st[2]))
		m.set_shader_parameter("polomer", float(meta[d]["polomer"]))
		m.set_shader_parameter("fade_od", bl - 8.0)   # náběh 10 m přes dithering plného stromu (bl - pr .. bl)
		m.set_shader_parameter("fade_do", 1600.0)
		m.set_shader_parameter("lod_daleko", Vector2(bl - pr * 0.5, pr))   # stejná mez jako LOD1, doplňkový dithering
		for bc: Vector2i in imp[d]:
			var list: Array = imp[d][bc]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			mm.mesh = quad
			mm.instance_count = list.size()
			var o := Vector3((bc.x + 0.5) * IMP_B, 0.0, (bc.y + 0.5) * IMP_B)
			var lo := Vector3(INF, INF, INF); var hi := -lo
			for i in list.size():
				var c: Color = list[i]
				c = Color(c.r - o.x, c.g, c.b - o.z, c.a)
				mm.set_instance_transform(i, Transform3D.IDENTITY)
				mm.set_instance_custom_data(i, c)
				lo = lo.min(Vector3(c.r, c.g, c.b)); hi = hi.max(Vector3(c.r, c.g, c.b))
			var r := float(meta[d]["polomer"]) * 3.0
			mm.custom_aabb = AABB(lo - Vector3(r, r, r), hi - lo + Vector3(r, r, r) * 2.0)
			var mi := MultiMeshInstance3D.new()
			mi.multimesh = mm; mi.material_override = m
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.position = o
			add_child(mi)
			n += list.size()
	print("impostory: %d stromů" % n)

func _mesh(cesta: String) -> Mesh:
	var sc: Node = load(cesta).instantiate()
	var mi: MeshInstance3D = sc.find_children("*", "MeshInstance3D", true, false)[0]
	var m: Mesh = mi.mesh
	sc.queue_free()   # ne free() – pád na tabletu (11. 11.)
	return m

## Listí (převzato z Havrana svet.gd _listi_shader + shaders/listi.gdshader, Míša 3. 11.: „střapáče zblízka“):
## normály od středu koruny – koruna se nasvítí jako objem, ne jako jednotlivé karty; vítr; zadní strana prosvítá;
## alfa roste s úrovní mipmapy (řídké listí z dálky nezmizí). zanik = (od, do) rozpouštění ditheringem jako _fade.
var _listi_sh: Shader
var _lod_mat: Array[ShaderMaterial] = []   # materiály s kamera_hrace (listí, kůra, impostory)
var _kura_sh: Shader
func _listi(m: Mesh, od := 0.0, do_ := 0.0, strom := true, lod := Vector3.ZERO, daleko := Vector2.ZERO) -> Mesh:
	if _listi_sh == null: _listi_sh = load("res://shaders/listi.gdshader")
	var mm: Mesh = m.duplicate(); var bb := m.get_aabb(); var c := bb.get_center()
	for i in mm.get_surface_count():
		var om := mm.surface_get_material(i)
		if om is BaseMaterial3D and (om as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED and (om as BaseMaterial3D).albedo_texture:
			var sm := ShaderMaterial.new(); sm.shader = _listi_sh; sm.resource_name = om.resource_name; _lod_mat.append(sm)
			sm.set_shader_parameter("barva", (om as BaseMaterial3D).albedo_texture)
			sm.set_shader_parameter("tint", (om as BaseMaterial3D).albedo_color)
			sm.set_shader_parameter("prah", maxf((om as BaseMaterial3D).alpha_scissor_threshold, 0.3))
			sm.set_shader_parameter("stred", Vector3(c.x, bb.position.y + bb.size.y * (0.62 if strom else 0.5), c.z))
			sm.set_shader_parameter("vyska", maxf(bb.end.y, 0.5))
			sm.set_shader_parameter("sila_vetru", 1.0 if strom else 0.6)
			sm.set_shader_parameter("objem", 0.65 if strom else 0.5)
			sm.set_shader_parameter("zanik", Vector2(od, do_)); sm.set_shader_parameter("lod_mez", lod); sm.set_shader_parameter("lod_daleko", daleko)
			mm.surface_set_material(i, sm)
		elif om is BaseMaterial3D and lod.z > 0.5:   # kůra: LOD po stromech (kura.gdshader) + rozpouštění do dálky
			if _kura_sh == null: _kura_sh = load("res://shaders/kura.gdshader")
			var b := om as BaseMaterial3D; var km := ShaderMaterial.new(); km.shader = _kura_sh; km.resource_name = om.resource_name; _lod_mat.append(km)
			km.set_shader_parameter("barva", b.albedo_texture); km.set_shader_parameter("tint", b.albedo_color)
			if b.normal_enabled and b.normal_texture: km.set_shader_parameter("normala", b.normal_texture); km.set_shader_parameter("ma_normalu", true)
			km.set_shader_parameter("zanik", Vector2(od, do_)); km.set_shader_parameter("lod_mez", lod); km.set_shader_parameter("lod_daleko", daleko)
			mm.surface_set_material(i, km)
		elif om is BaseMaterial3D and od != do_:   # kůra: dithering jako dřív
			var cm: BaseMaterial3D = om.duplicate(); cm.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_DITHER
			cm.distance_fade_min_distance = od; cm.distance_fade_max_distance = do_; mm.surface_set_material(i, cm)
	return mm

func _fade(m: Mesh, od: float, do_: float) -> Mesh:
	# kopie materiálů s distance fade (od < do = objevuje se s dálkou, od > do = mizí)
	var mm: Mesh = m.duplicate()
	for s in mm.get_surface_count():
		var mat := mm.surface_get_material(s)
		if mat is BaseMaterial3D:
			var c: BaseMaterial3D = mat.duplicate()
			c.distance_fade_mode = BaseMaterial3D.DISTANCE_FADE_PIXEL_DITHER
			c.distance_fade_min_distance = od
			c.distance_fade_max_distance = do_
			mm.surface_set_material(s, c)
	return mm

func _daleko(k: String, ts: Array, bl: float, pr: float) -> void:
	var m := _fade(_mesh("res://modely/stromy/%s_daleko.glb" % k), bl - pr, bl)
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = m
	mm.instance_count = ts.size()
	for i in ts.size(): mm.set_instance_transform(i, ts[i])
	var mi := MultiMeshInstance3D.new(); mi.multimesh = mm; mi.name = "daleko_" + k
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)

func _blizko(k: String, ts: Array, bl: float, pr: float, B: float, l0: float) -> void:
	# staré stromy (25–30 k troj.) i zblízka jako LOD1 – výkon i velikost APK (stare_lod1, docs/ab_srovnani.md)
	var stare_lod1 := k.ends_with("_stary") or k.ends_with("_stara")
	var m0 := _mesh("res://modely/stromy/%s.glb" % (k + "_lod1" if stare_lod1 else k))
	if stare_lod1:
		m0 = m0.duplicate()
	# LOD1 je importovaný bez textur (embedded_image_handling = Discard) – materiály z LOD0, ať nejsou v VRAM dvakrát
	if stare_lod1:
		var vzor: Mesh = _mesh("res://modely/stromy/%s.glb" % (k.split("_")[0] + "_stredni"))
		for s in mini(m0.get_surface_count(), vzor.get_surface_count()):
			m0.surface_set_material(s, vzor.surface_get_material(s))
	var m1raw: Mesh = _mesh("res://modely/stromy/%s_lod1.glb" % k).duplicate()
	for s in mini(m1raw.get_surface_count(), m0.get_surface_count()):
		m1raw.surface_set_material(s, m0.surface_get_material(s))
	var lp := float(cfg.get("lod_prolnuti_m", 3.0))   # LOD po stromech (Míša 10. 11.: blikání – dřív přepínala celá buňka)
	var m1 := _listi(m1raw, 0.0, 0.0, true, Vector3(l0, lp, 2.0), Vector2(bl - pr * 0.5, pr)) if cfg.get("listi_shader", true) else _fade(m1raw, bl, bl - pr)
	if cfg.get("listi_shader", true): m0 = _listi(m0, 0.0, 0.0, true, Vector3(l0, lp, 1.0))
	if cfg.get("jadro_koruny", 0.0) > 0.0: m0 = _jadro(m0, float(cfg["jadro_koruny"]))   # vnitřek koruny bez alfy (early-Z)
	var stin := _stin_proxy(m0) if cfg.get("stin_proxy", true) else null   # stín z hrubé koruny, ne z listí (2. průchod listí)
	# blízké stromy jen v buňkách kolem hráče (bunky_kolem.gd – pád na tabletu 11. 11.: buňky na celou mapu = došla paměť)
	if _blizke == null:
		_blizke = BunkyKolem.new(); _blizke.name = "Blizko"; _blizke.B = B; _blizke.R = bl + B * 0.75 + 4.0
		_blizke.vyrob = _vyrob_blizko; add_child(_blizke)
	var sada := _bl_sady.size()
	_bl_sady.append({"m0": m0, "m1": m1, "stin": stin,
		"v0": Vector2(0.0, l0 + lp + B * 0.75), "v1": Vector2(maxf(0.0, l0 - lp - B * 0.75), bl + B * 0.75)})
	for t in ts: _blizke.pridej(t, sada)

const BunkyKolem := preload("res://scripts/bunky_kolem.gd")
var _blizke: Node3D
var _bl_sady := []      # [{m0, m1, stin, v0, v1}] – sítě a dosahy viditelnosti jedné varianty

## Uzly jedné varianty v jedné buňce: LOD0 do l0, LOD1 od l0 do bl (dosahy na střed buňky ± půl úhlopříčky);
## o úroveň rozhoduje shader po stromech (lod_mez), stínové těleso jen do stin_dosah_m
func _vyrob_blizko(sada: int, buf: PackedFloat32Array, n: int) -> Array:
	var sd: Dictionary = _bl_sady[sada]; var out := []
	for lod in 2:
		var mi := BunkyKolem.mmi(sd["m0"] if lod == 0 else sd["m1"], buf, n)
		var v: Vector2 = sd["v0"] if lod == 0 else sd["v1"]
		mi.visibility_range_begin = v.x; mi.visibility_range_end = v.y
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if sd["stin"] else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		out.append(mi)
	if sd["stin"]:
		var si := BunkyKolem.mmi(sd["stin"], buf, n); si.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		si.visibility_range_end = float(cfg.get("stin_dosah_m", 45.0)); si.visibility_range_end_margin = 4.0
		out.append(si)
	return out


## Pata kmene (stromy_modely.json zapusteni): na svahu zapustit o pokles terénu na obvodu kořenového náběhu, ať kmen nevisí
func _pata(x: float, z: float, h: float, sc: float) -> float:
	var zp: Dictionary = cfg.get("zapusteni", {})
	var y0: float = svet.vyska(x, z)
	var r := maxf(float(_kr.get("min_m", 0.12)), h * float(_kr.get("na_m_vysky", 0.012))) * float(zp.get("obvod_nasobek", 1.4))
	var mn := y0
	for u in 8:
		mn = minf(mn, svet.vyska(x + r * cos(u * PI / 4), z + r * sin(u * PI / 4)))
	return y0 - maxf(float(zp.get("zaklad_m", 0.15)) * sc, y0 - mn + float(zp.get("rezerva_m", 0.05)))


## Jádro koruny (Míša 10. 11.: „aplikuj, co víš“ – overdraw listí je hlavní brzda lesa na tabletu): trojúhelníky listí,
## jejichž těžiště leží uvnitř elipsoidu koruny (poměr k), dostanou shader bez alfy a discard (listi_jadro.gdshader) –
## GPU je odmítne testem hloubky dřív, než je stínuje; obrys koruny zůstává průhledný (listi.gdshader).
var _jadro_sh: Shader
func _jadro(m: Mesh, k: float) -> Mesh:
	if _jadro_sh == null: _jadro_sh = load("res://shaders/listi_jadro.gdshader")
	var out := ArrayMesh.new()
	for i in m.get_surface_count():
		var mat := m.surface_get_material(i); var ar := m.surface_get_arrays(i)
		if not (mat is ShaderMaterial and (mat as ShaderMaterial).shader == _listi_sh) or ar[Mesh.ARRAY_INDEX] == null:
			out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, ar); out.surface_set_material(out.get_surface_count() - 1, mat); continue
		var v: PackedVector3Array = ar[Mesh.ARRAY_VERTEX]; var ix: PackedInt32Array = ar[Mesh.ARRAY_INDEX]
		var bb := AABB(v[0], Vector3.ZERO)
		for p in v: bb = bb.expand(p)
		var c := bb.get_center(); var r := bb.size * 0.5
		r = Vector3(maxf(r.x, 0.1), maxf(r.y, 0.1), maxf(r.z, 0.1))
		var vn := PackedInt32Array(); var ob := PackedInt32Array()
		for t in range(0, ix.size(), 3):
			var q := (v[ix[t]] + v[ix[t + 1]] + v[ix[t + 2]]) / 3.0 - c
			var d := Vector3(q.x / r.x, q.y / r.y, q.z / r.z).length()
			var cil := vn if d < k else ob
			cil.append(ix[t]); cil.append(ix[t + 1]); cil.append(ix[t + 2])
		for cast in [[ob, mat], [vn, null]]:
			if (cast[0] as PackedInt32Array).is_empty(): continue
			var a2 := ar.duplicate(); a2[Mesh.ARRAY_INDEX] = cast[0]
			out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a2)
			var mm: Material = cast[1]
			if mm == null:
				var jm := ShaderMaterial.new(); jm.shader = _jadro_sh
				for pn in ["barva", "tint", "stred", "vyska", "sila_vetru", "objem"]: jm.set_shader_parameter(pn, (mat as ShaderMaterial).get_shader_parameter(pn))
				mm = jm
			out.surface_set_material(out.get_surface_count() - 1, mm)
	return out

## Stínové těleso stromu: elipsoid koruny (obal listí × 0,85) + válec kmene – stín slunce bez druhého kreslení listí.
func _stin_proxy(m: Mesh) -> Mesh:
	var lb := AABB(); var prvni := true; var vy := 0.0
	for i in m.get_surface_count():
		var mat := m.surface_get_material(i); var v: PackedVector3Array = m.surface_get_arrays(i)[Mesh.ARRAY_VERTEX]
		for p in v: vy = maxf(vy, p.y)
		if not (mat is ShaderMaterial): continue
		for p in v:
			if prvni: lb = AABB(p, Vector3.ZERO); prvni = false
			else: lb = lb.expand(p)
	if prvni: return null
	var st := SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var sf := SphereMesh.new(); sf.radial_segments = 10; sf.rings = 6; sf.radius = 0.5; sf.height = 1.0
	st.append_from(sf, 0, Transform3D(Basis.from_scale(lb.size * 0.85), lb.get_center()))
	var kv := CylinderMesh.new(); kv.radial_segments = 6; kv.rings = 1
	var rk := maxf(0.12, vy * 0.012); kv.top_radius = rk; kv.bottom_radius = rk * 1.3; kv.height = maxf(lb.position.y + lb.size.y * 0.3, 0.5)
	st.append_from(kv, 0, Transform3D(Basis(), Vector3(lb.get_center().x, kv.height * 0.5, lb.get_center().z)))
	return st.commit()
