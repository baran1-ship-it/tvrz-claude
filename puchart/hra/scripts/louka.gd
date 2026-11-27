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
var _kr: Image = null   # krytí korun (nastroje/kryt_korun.py)
var LS_: Dictionary = {}
var bunky := {}            # Vector3i(x, z, vrstva) -> MultiMeshInstance3D / null (prázdná)
var _ceka := {}            # Vector3i(x, z, vrstva) -> id úlohy
## Vrstvy rozsevu (plán E1, Míša 18.–20. 11., předloha docs/reference/lod_trava_video): 0 jemné trsy blízko (louka.json),
## 1 střední pás – karty s pečenou texturou porostu (louka.json pas, trava_pas_atlas.png, stebla.gdshader rezim 2).
## Každá: [síť, buňka m, dosah m, krok m, tabulka druhů, výchozí druhy]
var _vrstvy: Array = []
var _pas: Mesh = null
var pas_nasobek := 1.0     # automatika detailu (regulator.gd pas_dosah): násobek dosahu pásu – méně buněk = méně troj.
var _hotove: Array = []
var _zamek := Mutex.new()
const ZasobaMM := preload("res://scripts/zasoba_mm.gd")
const ATLAS_POMER := 341.0 / 256.0   # Havran: šířka : výška buňky atlasu (3×2, 1024×512)

func postav(s: Node3D, kamera: Camera3D) -> void:
	svet = s; cam = kamera
	cfg = JSON.parse_string(FileAccess.get_file_as_string("res://data/louka.json"))
	sj = JSON.parse_string(FileAccess.get_file_as_string("res://data/stanoviste.json"))
	st = load("res://data/stanoviste.png").get_image()
	if ResourceLoader.exists("res://textury/maska_cesty.png"): _mc = (load("res://textury/maska_cesty.png") as Texture2D).get_image()
	_kc = cfg.get("kraj_cesty", {})   # plán C2: krajnice střídá holou hlínu, trávu a květy po úsecích (louka.json kraj_cesty)
	if not _kc.is_empty(): _kc_sum.seed = int(_kc["seed"]); _kc_sum.frequency = 1.0 / float(_kc["usek_m"])
	_trs = _karta_mesh(3, ATLAS_POMER, 1.0)
	LS_ = cfg.get("les", {})
	if ResourceLoader.exists("res://data/kryt.png"):
		_kr = load("res://data/kryt.png").get_image()
		if _kr.is_compressed(): _kr.decompress()
	var m := _trs.surface_get_material(0) as ShaderMaterial
	m.set_shader_parameter("z_custom", true)
	if cfg.has("ohyb"): m.set_shader_parameter("ohyb_sila", Vector2(float(cfg["ohyb"]["sila"][0]), float(cfg["ohyb"]["sila"][1])))   # plán C6
	m.set_shader_parameter("hust_od", float(cfg["hust_od_m"])); m.set_shader_parameter("hust_do", float(cfg["hust_do_m"]))
	var ko: Array = cfg.get("konec_m", [cfg["hust_do_m"], float(cfg["hust_do_m"]) + 30.0])
	m.set_shader_parameter("hust_konec", float(ko[0])); m.set_shader_parameter("konec_sirka", float(ko[1]) - float(ko[0]))
	m.set_shader_parameter("hust_zbytek", float(cfg.get("hust_zbytek", 0.0)))
	m.set_shader_parameter("prechod_trsu", float(cfg.get("prechod_trsu", 0.1)))
	_vrstvy = [[_trs, float(cfg["bunka_m"]), float(cfg["dosah_m"]), float(cfg["krok_m"]), cfg["druhy"], int(cfg.get("nove_za_snimek", 1))]]
	var P: Dictionary = cfg.get("pas", {})
	if bool(P.get("zapnuto", false)) and ResourceLoader.exists(str(P["atlas"]["soubor"])):
		var A: Dictionary = P["atlas"]
		_pas = _karta_mesh(int(P.get("karty", 3)), float(A["bunka_px"][0]) / float(A["bunka_px"][1]), 1.0)
		var pm := _pas.surface_get_material(0) as ShaderMaterial
		pm.set_shader_parameter("atlas", load(str(A["soubor"])))
		pm.set_shader_parameter("sloupce", float(A["sloupce"])); pm.set_shader_parameter("radky", float(A["radky"]))
		pm.set_shader_parameter("z_custom", true); pm.set_shader_parameter("rezim", 2)
		pm.set_shader_parameter("vyska_od", float(P["vyska_m"][0])); pm.set_shader_parameter("vyska_do", float(P["vyska_m"][1]))
		pm.set_shader_parameter("pas_od", Vector2(float(P["od_m"][0]), float(P["od_m"][1])))
		pm.set_shader_parameter("hust_konec", float(P["do_m"][0])); pm.set_shader_parameter("konec_sirka", float(P["do_m"][1]) - float(P["do_m"][0]))
		pm.set_shader_parameter("hust_od", 1e5); pm.set_shader_parameter("hust_do", 1e5 + 1.0)
		pm.set_shader_parameter("vitr", 0.6)
		pm.set_shader_parameter("prechod_trsu", float(cfg.get("prechod_trsu", 0.1)))
		_vrstvy.append([_pas, float(P["bunka_m"]), float(P["dosah_m"]), float(P["krok_m"]), P["druhy"], int(P.get("nove_za_snimek", 1))])
		print("LOUKA střední pás %s–%s m, buňka %s m, krok %s m" % [P["od_m"], P["do_m"], P["bunka_m"], P["krok_m"]])

	if str(cfg.get("rezim", "bunky")) == "mrizka": _mrizka_postav()
	nastav_unshaded(_un_vychozi())

## ---- TRÁVA UNSHADED (louka.json unshaded; Havran scripts/louka.gd _stebla_shader/_svetlo_travy, modely.json trava_unshaded):
## v Compatibility dostane každý osvětlený materiál při stínovaném slunci druhý průchod (gles3 rasterizer_scene_gles3.cpp
## uses_additive_lighting; render_mode shadows_disabled ho nevypne) – Havran tablet: ~60 % ceny trávy (louka p50 28 → 21 ms).
## Unshaded tráva ho nemá; světlo (okolí + slunce × (1 − stin_korun × zápoj)) počítá _svetlo_travy z denní doby.
var _un := false
var _shader_un: Shader
var _un_t := 0.0
func _un_vychozi() -> bool:
	var e := OS.get_environment("PUCHART_TRAVA_UNSHADED")   # PC: A/B a kalibrace barvy (1 / 0)
	if e != "": return e == "1"
	var u: Dictionary = cfg.get("unshaded", {})
	return bool(u.get("tablet", false)) if OS.has_feature("mobile") else bool(u.get("pc", false))

func _materialy() -> Array:
	var a := []
	for m in vsechny_site(): a.append((m as Mesh).surface_get_material(0))
	return a

func nastav_unshaded(on: bool) -> void:   # také varianta měřicí trasy (mereni.json "trava_unshaded")
	_un = on
	var sh0: Shader = load("res://shaders/stebla.gdshader")
	if on and _shader_un == null:
		_shader_un = Shader.new(); _shader_un.code = sh0.code.replace("vertex_lighting,", "unshaded,")
	var kr_t: Texture2D = load("res://data/kryt.png") if ResourceLoader.exists("res://data/kryt.png") else null
	for mat: ShaderMaterial in _materialy():
		mat.shader = _shader_un if on else sh0
		if on and kr_t:
			mat.set_shader_parameter("kryt", kr_t)
			mat.set_shader_parameter("stan_info", Vector4(float(sj["x0_hra"]), float(sj["z0_hra"]), float(sj["krok_m"]), st.get_width()))
		if not on:
			mat.set_shader_parameter("svetlo", Vector3.ONE); mat.set_shader_parameter("slunce", Vector3.ZERO); mat.set_shader_parameter("stin_korun", 0.0)
	_un_t = 0.0
	print("LOUKA tráva unshaded %s (materiálů %d)" % [on, _materialy().size()])

func _svetlo_travy(dt: float) -> void:
	_un_t -= dt
	if not _un or _un_t > 0.0: return
	_un_t = 0.5
	var den: Node = get_tree().current_scene.get("den") if get_tree().current_scene else null
	if den == null or den.get("slunce") == null: return
	var sun: DirectionalLight3D = den.slunce; var env: Environment = den.env; var sky: ShaderMaterial = den.obloha
	var u: Dictionary = cfg["unshaded"]
	# Havran _svetlo_travy: slunce = barva (lin.) × energie × Lambert s obalem (diffuse_lambert_wrap, normála nahoru);
	# okolí = obloha (horizont → zenit, váha obloha_zenit) × energie oblohy × ambient × podíl oblohy + barva okolí × (1 − podíl)
	var s := sun.global_transform.basis.z.normalized()
	var el := maxf(s.y, 0.0); var ob := float(u["obal"])
	var sl := sun.light_color.srgb_to_linear() * sun.light_energy * ((el + ob) / ((1.0 + ob) * (1.0 + ob)) if el > 0.0 and sun.visible else 0.0)
	var zen: Color = (sky.get_shader_parameter("zenith") as Color).srgb_to_linear()
	var hor: Color = (sky.get_shader_parameter("horizon") as Color).srgb_to_linear()
	var sp := env.ambient_light_sky_contribution
	var en: Variant = sky.get_shader_parameter("energy")   # neseřízený uniform = null → výchozí 1,0 (sky.gdshader)
	var ok := hor.lerp(zen, float(u["obloha_zenit"])) * (1.0 if en == null else float(en)) * env.ambient_light_energy * sp \
			+ env.ambient_light_color.srgb_to_linear() * env.ambient_light_energy * (1.0 - sp)
	var ks: Array = u["slunce_x"]; var ko: Array = u["okoli_x"]
	var vs := Vector3(sl.r * float(ks[0]), sl.g * float(ks[1]), sl.b * float(ks[2]))
	var vo := Vector3(ok.r * float(ko[0]), ok.g * float(ko[1]), ok.b * float(ko[2]))
	for mat: ShaderMaterial in _materialy():
		mat.set_shader_parameter("svetlo", vo); mat.set_shader_parameter("slunce", vs); mat.set_shader_parameter("stin_korun", float(u["stin_korun"]))
	if OS.get_environment("PUCHART_TRAVA_LADENI") != "": print("LOUKA světlo unshaded okolí ", vo, " slunce ", vs, " el ", el)

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
		m.set_shader_parameter("hust_konec", float(cfg["hust_do_m"])); m.set_shader_parameter("hust_zbytek", float(cfg.get("hust_zbytek", 0.0)))
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

## Automatika detailu (regulator.gd pas_dosah, rozpocty.json stupeň 1): dosah středního pásu × f – buňky za ním se
## uvolní (méně troj.), konec v shaderu se posune stejně (karty mizí po jedné, ne hrana buněk). 1 = podle louka.json.
func nastav_pas(f: float) -> void:
	pas_nasobek = f
	if _pas == null: return
	var P: Dictionary = cfg["pas"]
	var m := _pas.surface_get_material(0) as ShaderMaterial
	m.set_shader_parameter("hust_konec", float(P["do_m"][0]) * f); m.set_shader_parameter("konec_sirka", (float(P["do_m"][1]) - float(P["do_m"][0])) * f)

func vsechny_site() -> Array: return [_trs] + ([_pas] if _pas else []) + _prst.map(func(q): return (q[0] as MultiMeshInstance3D).multimesh.mesh)

var _mc: Image = null   # maska cest (hlína R/G) – krajnice cest
var _kc: Dictionary = {}; var _kc_sum := FastNoiseLite.new()   # úseky krajnice (plán C2, stejný šum jako byliny.gd)
func _trida(x: float, z: float) -> String:
	var c := int((x - float(sj["x0_hra"])) / float(sj["krok_m"])); var r := int((z - float(sj["z0_hra"])) / float(sj["krok_m"]))
	if c < 0 or r < 0 or c >= st.get_width() or r >= st.get_height(): return ""
	return sj["tridy"][int(st.get_pixel(c, r).r8)]

var _les = null
func _process(_d: float) -> void:
	if cam == null or _trs == null: return
	_svetlo_travy(_d)
	# časované prolnutí trsů (Míša 27. 11. „doskakovala tráva“): poloha kamery před 0,25 s z lesa (les.gd _kamera_pred)
	if _les == null: _les = get_tree().root.find_child("Les", true, false)
	var lc_: float = 1.0 if (_les != null and _les.cfg.get("lod_casove", {}).get("zapnuto", false) and OS.get_environment("PUCHART_LOD_PASMO") == "") else 0.0
	var kpr: Vector3 = _les.kamera_pred_ted if _les != null else cam.global_position
	for mt_: Variant in [_trs.surface_get_material(0), _pas.surface_get_material(0) if _pas != null else null]:
		if mt_ is ShaderMaterial: (mt_ as ShaderMaterial).set_shader_parameter("kamera_pred", kpr); (mt_ as ShaderMaterial).set_shader_parameter("lod_cas", lc_)
	var oh: Dictionary = cfg.get("ohyb", {})   # plán C6: tráva se ohýbá od hráče (jemné trsy, stebla.gdshader ohyb_hrac)
	if not oh.is_empty() and bool(oh.get("zapnuto", true)):
		var pc := cam.global_position
		(_trs.surface_get_material(0) as ShaderMaterial).set_shader_parameter("ohyb_hrac", Vector4(pc.x, pc.y - float(oh["oci_m"]), pc.z, float(oh["polomer_m"])))
	if not _prst.is_empty(): _mrizka_tick(); return
	var p := cam.global_position
	for li in _vrstvy.size():
		var V: Array = _vrstvy[li]
		var B: float = V[1]; var R: float = V[2] * (pas_nasobek if li == 1 else 1.0)
		var c0 := Vector2i(int(floor(p.x / B)), int(floor(p.z / B))); var n := int(ceil(R / B))
		var nove := 0
		for i in range(-n, n + 1):
			for j in range(-n, n + 1):
				var k := Vector3i(c0.x + i, c0.y + j, li)
				if bunky.has(k) or _ceka.has(k): continue
				var stred := Vector2((k.x + 0.5) * B, (k.y + 0.5) * B)
				if stred.distance_to(Vector2(p.x, p.z)) > R + B * 0.71: continue
				if nove >= int(V[5]) * 2: continue
				_ceka[k] = WorkerThreadPool.add_task(_rozsej.bind(k)); nove += 1
		for k: Vector3i in bunky.keys():   # uvolnit vzdálené (hystereze 0,5 buňky – menší buňky jemných trsů, plán E1)
			if k.z != li: continue
			var stred := Vector2((k.x + 0.5) * B, (k.y + 0.5) * B)
			if stred.distance_to(Vector2(p.x, p.z)) > R + B * 1.2:
				if bunky[k] != null: ZasobaMM.vrat_strom(bunky[k]); bunky[k].queue_free()
				bunky.erase(k)
	_zamek.lock(); var hot := _hotove.duplicate(); _hotove.clear(); _zamek.unlock()
	for h in hot: _vloz(h)

func _rozsej(k: Vector3i) -> void:
	var V: Array = _vrstvy[k.z]
	var B: float = V[1]; var krok: float = V[3]
	var rng := RandomNumberGenerator.new(); rng.seed = hash(Vector3i(k.x * 7919, k.y * 104729, k.z * 31))
	var tridy: Dictionary = cfg["tridy"]; var druhy: Dictionary = V[4]
	var cust := PackedFloat32Array(); var x0 := k.x * B; var z0 := k.y * B
	var cx := x0 + B * 0.5; var cz := z0 + B * 0.5
	var z := 0.0
	while z < B:
		var x := 0.0
		while x < B:
			var px := x0 + x + rng.randf_range(-0.45, 0.45) * krok; var pz := z0 + z + rng.randf_range(-0.45, 0.45) * krok
			var tr := _trida(px, pz); var h := float(tridy.get(tr, 0.0))
			if tr == "cesta" and _mc != null:   # Míša 19. 11.: třída cesta je širší než vyjetá hlína – krajnice zarostlé, holá jen hlína z masky cest
				var mcx := clampi(int((px - float(sj["x0_hra"])) / float(sj["krok_m"]) * _mc.get_width() / st.get_width()), 0, _mc.get_width() - 1)
				var mcz := clampi(int((pz - float(sj["z0_hra"])) / float(sj["krok_m"]) * _mc.get_height() / st.get_height()), 0, _mc.get_height() - 1)
				var pc := _mc.get_pixel(mcx, mcz); h = float(tridy.get("cesta_krajnice", 0.0)) * (1.0 - smoothstep(0.08, 0.35, pc.r + pc.g))
				if h > 0.0 and not _kc.is_empty():   # C2: úsek holé hlíny (s kameny – byliny.gd) / trávy / květů podle šumu podél cesty
					var ku := _kc_sum.get_noise_2d(px, pz) * 0.5 + 0.5
					if ku < float(_kc["hola_do"]): h *= float(_kc["hola_trava"])
					elif ku > float(_kc["kvety_od"]) and druhy.has("cesta_kvety"): tr = "cesta_kvety"
			if h > 0.0 and _kr != null:   # zápoj korun (kryt.png, Havran les_podrost.json trava): pod zápojem ≈ 0, světliny jako louka; samotný strom v louce zápoj nemá
				var kc := clampi(int((px - float(sj["x0_hra"])) / float(sj["krok_m"])), 0, _kr.get_width() - 1)
				var kz := clampi(int((pz - float(sj["z0_hra"])) / float(sj["krok_m"])), 0, _kr.get_height() - 1)
				h *= 1.0 - float(LS_.get("ubytek", 0.985)) * smoothstep(float(LS_.get("kryt_od", 0.3)), float(LS_.get("kryt_do", 0.8)), _kr.get_pixel(kc, kz).r)
			if h > 0.0 and rng.randf() < h:
				var pod: Array = druhy.get(tr, druhy["_"]); var u := rng.randf(); var druh := 0; var acc := 0.0
				for di in pod.size():
					acc += float(pod[di])
					if u <= acc: druh = di; break
				var hs := rng.randf() * 0.999
				var y: float = svet.vyska(px, pz) - 0.04
				if k.z == 1:   # karta pásu je ~2,4 m široká: natočení a zkosení podle svahu v transformaci instance (custom je v Compatibility jen half float) – spodní hrana leží na zemi, nevisí ani se nezaboří
					var r := float(cfg["pas"].get("pata_r_m", 1.3))
					var gx := clampf((svet.vyska(px + r, pz) - svet.vyska(px - r, pz)) / (2.0 * r), -1.5, 1.5)
					var gz := clampf((svet.vyska(px, pz + r) - svet.vyska(px, pz - r)) / (2.0 * r), -1.5, 1.5)
					var a := rng.randf() * TAU; var ca := cos(a); var sa := sin(a)
					y -= float(cfg["pas"].get("ponor_m", 0.04))
					cust.append_array([ca, 0.0, sa, 0.0, gx * ca - gz * sa, 1.0, gx * sa + gz * ca, 0.0, -sa, 0.0, ca, 0.0, float(druh) + hs, px - cx, y, pz - cz])
				else:
					cust.append_array([1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, float(druh) + hs, px - cx, y, pz - cz])   # formát MultiMesh.buffer: jednotková transformace + custom (zásoba MM)   # formát MultiMesh.buffer: jednotková transformace + custom (zásoba MM)
			x += krok
		z += krok
	_zamek.lock(); _hotove.append([k, cust]); _zamek.unlock()

func _vloz(h: Array) -> void:
	var k: Vector3i = h[0]; var cust: PackedFloat32Array = h[1]
	if _ceka.has(k): WorkerThreadPool.wait_for_task_completion(_ceka[k]); _ceka.erase(k)
	var n := cust.size() / 16
	if n == 0: bunky[k] = null; return
	var V: Array = _vrstvy[k.z]; var B: float = V[1]
	var mm := ZasobaMM.vezmi(V[0], cust, n, true, AABB(Vector3(-B * 0.5 - 2, -200, -B * 0.5 - 2), Vector3(B + 4, 400, B + 4)))
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
