extends RefCounted
## Svet tvrze vymodelovany v Blenderu (blender/export_game.py): nacte modely/tvrz.glb,
## priradi materialy podle jmen, postavi kolize, rostliny (MultiMesh po bunkach) a predá
## informace o ohnich, mistnostech a pouzitelnych vecech hernimu zivotu (life.gd).

const MOD := "res://modely/"
const BARVA_LOUKY := Vector3(0.145, 0.235, 0.02)   # linearne; kalibrace testem dalka (tools/test_svet.gd)
const BARVA_LESA := Vector3(0.062, 0.095, 0.015)
const BUNKA := 24.0
## textury s vyskovou mapou -> parallax (hloubka v metrech)
const HLOUBKA := {"dlazba": 0.04, "dlazba_hrad": 0.035, "kocicky": 0.05, "piskovec": 0.02, "podlaha": 0.008, "prkna_ven": 0.012, "sindel": 0.035, "skala_piskovec": 0.07, "kamen": 0.04, "kamen_lisejnik": 0.05}

var info: Dictionary
var data: Dictionary
var sum: NoiseTexture2D
var _tex := {}
var _mats := {}
var water_y := -2.75
var water_mat: ShaderMaterial          # hladina prikopu (kruhove vlnky)
## rostliny ke sberu: druh rostliny ve svete -> predmet v brasne; kazda instance je sberne misto (sber.gd)
const SBER := {"nettle_plant": "kopriva", "celandine_01": "vlastovicnik", "periwinkle_plant": "barvinek"}
var grass_mesh: Mesh                   # trs travy (3 karty) i pro travu v krajine (trava.gd)
var sber_spots: Array = []             # {"id", "mmi", "i", "xf"}
var vodni: Array = []                  # materialy vody (vlnky a ceřeni od hrace nastavuje voda.gd)
const VRSTVA_VODA := 1 << 19           # plochy hladin jako Area3D (zjisteni, ze hrac stoji ve vode)


func _init(p_info: Dictionary) -> void:
	info = p_info


func build(parent: Node3D, quality: int) -> void:
	var f := FileAccess.open(MOD + "svet.json", FileAccess.READ)
	data = JSON.parse_string(f.get_as_text())
	water_y = float(data.get("voda_y", -2.75))
	_make_noise()
	var scene: PackedScene = load(MOD + "tvrz.glb")
	var root := scene.instantiate()
	root.name = "Tvrz"
	parent.add_child(root)
	_koryto_terenu(root)
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		_apply_materials(mi)
		# oboustranne stiny: tenke vrstvy (omitka uvnitr, prkna) jinak propousteji svetlo ve skvirach
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		var nm := String(mi.name)
		if nm == "Reka_voda" and FileAccess.file_exists("res://modely/reka/reka.res"):
			mi.visible = false               # potok: Waterways (_reka), mrizkova hladina se zubatym brehem pryc
		if nm == "Teren_cesta_kamen":
			mi.visible = false               # tmave kocici hlavy pres cestu s ostrou hranou (Misa 17. 10.): pod nimi je cesta
			continue
		if nm == "Skaly":
			mi.visible = false               # zaoblene balvany u tvrze: textura ze sveta v "letokruzich" (Misa: smazat)
		if nm == "Most_potok":
			_most_kuly(mi)
			_most_podlozka(mi)
		# sukne jemne site jen pro oko: jako kolize byla svislou stenou na okraji Teren_most (test prochod, breh potoka)
		if (nm.begins_with("Teren") or nm.begins_with("Nadvori")) and not nm.ends_with("_sukne"):
			_trimesh(mi)
		if nm.begins_with("Teren") or nm.begins_with("Reka") or nm.begins_with("Ruiny") or nm.begins_with("Skaly") \
				or nm.ends_with("_zahrady") or nm.begins_with("Hnojiste"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # rozpocet: teren, voda, ruiny, zahrady nekreslit do stinu
		if nm.begins_with("Rakos") or nm.begins_with("Slama"):
			mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mi.visibility_range_end = 70.0
	_reka(parent)
	_zaplaty(root)
	_kontrola_hladiny(parent)
	_collisions(parent)
	_static_items(parent)
	_info()
	_plants(parent, quality)
	_ves_grass(parent, quality)
	_rozdel_site(root)


# ------------------------------------------------------------------ deleni velkych siti (0.60)

## Velke sloucene site tvrz.glb (teren, ves, rakos, ochozy, ruiny - az 1400 m) se kreslily cele, kdykoli byl videt
## kousek: zadne orezani pohledem ani LOD (prikop 2,8 M troj.). Po stavbe sveta (koryto, kolize, rostliny pouzily
## puvodni site) se rozdeli na ctverce a kazdy dostane LOD; puvodni sit se uvolni, jeji kolize zustava.
const DELIT_OD := 60.0                 # site vetsi nez 60 m a s vic nez 8000 troj.
const DELIT_TROJ := 8000


func _rozdel_site(root: Node3D) -> void:
	if OS.has_environment("TVRZ_NEDELIT"):
		return
	var t0 := Time.get_ticks_msec()
	var vody := {}
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var me := (mi as MeshInstance3D).mesh
		if me == null:
			continue
		for i in me.get_surface_count():
			var mt := me.surface_get_material(i)
			if mt and String(mt.resource_name).begins_with("voda"):
				vody[mi] = true                  # hladiny drzi nadrz.gd (shader, hloubka) - nedelit
	var n_siti := 0
	var n_kusu := 0
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D
		var nm := String(mi.name)
		if mi.mesh == null or not mi.visible or vody.has(mi) or nm.begins_with("Pohyb") or mi.mesh.get_blend_shape_count() > 0:
			continue
		# teren se nedeli (0.62): ImporterMesh.generate_lods v behu hry LOD nevytvori (0 urovni, overeno), takze bezove
		# plachty a pyramidy 0.60 a bledé skvrny na kopcich 0.61 delalo samo deleni terenu - teren zustava cely
		if nm.begins_with("Teren"):
			continue
		var bb := mi.mesh.get_aabb()
		var vel := maxf(bb.size.x, bb.size.z)
		var troj := 0
		for i in mi.mesh.get_surface_count():
			troj += mi.mesh.surface_get_array_index_len(i) / 3
		if vel < DELIT_OD or troj < DELIT_TROJ:
			# 0.60: stavby tvrze bez LOD z importu (Ochozy 55 k, vrata 2x 22 k, VezDrevo 36 k...) - dogenerovat
			continue
		var krok := clampf(vel / 5.0, 128.0, 640.0)        # 0.60: vel/10 (64 m) = prikop 1770 kresleni; vetsi ctverce
		var nk := _rozdel(mi, krok)
		print("  deleni %s: %d troj, %.0f m -> %d kusu po %.0f m" % [nm, troj, vel, nk, krok])
		n_kusu += nk
		n_siti += 1
	print("deleni siti: %d siti -> %d kusu, %d ms" % [n_siti, n_kusu, Time.get_ticks_msec() - t0])


func _rozdel(mi: MeshInstance3D, krok: float) -> int:
	var me := mi.mesh
	var kusy := {}                                   # Vector2i -> [[pole povrchu, material], ...]
	for s in me.get_surface_count():
		var a := me.surface_get_arrays(s)
		var mat := mi.get_active_material(s)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		if idx.is_empty():
			idx.resize(v.size())
			for i in v.size():
				idx[i] = i
		# trojuhelniky podle ctverce teziste
		var podle := {}
		for t in idx.size() / 3:
			var c := (v[idx[t * 3]] + v[idx[t * 3 + 1]] + v[idx[t * 3 + 2]]) / 3.0
			var k := Vector2i(floori(c.x / krok), floori(c.z / krok))
			if not podle.has(k):
				podle[k] = []
			(podle[k] as Array).append(t)
		var mapa := PackedInt32Array()
		mapa.resize(v.size())
		mapa.fill(-1)
		for k: Vector2i in podle:
			var tr: Array = podle[k]
			var pouzite := PackedInt32Array()
			var ni := PackedInt32Array()
			ni.resize(tr.size() * 3)
			for j in tr.size():
				for e in 3:
					var vi := idx[tr[j] * 3 + e]
					if mapa[vi] < 0:
						mapa[vi] = pouzite.size()
						pouzite.append(vi)
					ni[j * 3 + e] = mapa[vi]
			for vi in pouzite:
				mapa[vi] = -1
			var na := []
			na.resize(Mesh.ARRAY_MAX)
			na[Mesh.ARRAY_INDEX] = ni
			for ai in [Mesh.ARRAY_VERTEX, Mesh.ARRAY_NORMAL, Mesh.ARRAY_TANGENT, Mesh.ARRAY_COLOR, Mesh.ARRAY_TEX_UV, Mesh.ARRAY_TEX_UV2]:
				if a[ai] == null:
					continue
				var src = a[ai]
				var sl := 4 if ai == Mesh.ARRAY_TANGENT else 1
				var dst = src.slice(0, 0)              # prazdne pole stejneho typu (duplicate by kopiroval cele)
				dst.resize(pouzite.size() * sl)
				for j in pouzite.size():
					for q in sl:
						dst[j * sl + q] = src[pouzite[j] * sl + q]
				na[ai] = dst
			if not kusy.has(k):
				kusy[k] = []
			(kusy[k] as Array).append([na, mat])
	for k: Vector2i in kusy:
		var im := ImporterMesh.new()
		for pv: Array in kusy[k]:
			im.add_surface(Mesh.PRIMITIVE_TRIANGLES, pv[0], [], {}, pv[1])
		var kus := MeshInstance3D.new()
		kus.name = "%s_k%d_%d" % [mi.name, k.x, k.y]
		kus.mesh = im.get_mesh()
		kus.transform = mi.transform
		kus.cast_shadow = mi.cast_shadow
		kus.visibility_range_end = mi.visibility_range_end
		kus.visibility_range_end_margin = mi.visibility_range_end_margin
		kus.visibility_range_fade_mode = mi.visibility_range_fade_mode
		mi.get_parent().add_child(kus)
	mi.mesh = null
	return kusy.size()


# ------------------------------------------------------------------ materialy

func _make_noise() -> void:
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = 0.012
	fn.fractal_octaves = 5
	sum = NoiseTexture2D.new()
	sum.width = 512
	sum.height = 512
	sum.seamless = true
	sum.noise = fn
	sum.generate_mipmaps = true


func _t(name: String, kind: String) -> Texture2D:
	var key := "%s_%s" % [name, kind]
	if not _tex.has(key):
		_tex[key] = load(MOD + "textury/%s.jpg" % key)
	return _tex[key]


var _alb := {}


func _albedo() -> Dictionary:
	if _alb.is_empty() and FileAccess.file_exists(MOD + "textury/albedo.json"):
		_alb = JSON.parse_string(FileAccess.get_file_as_string(MOD + "textury/albedo.json"))
	return _alb


func _size(name: String) -> float:
	var s: Array = data["textury"].get(name, [2.0, 2.0])
	return float(s[0])


func material(name: String) -> Material:
	var base := name.split(".")[0]
	if _mats.has(base):
		return _mats[base]
	var d: Dictionary = data["materialy"].get(base, {})
	var m: Material
	if base == "popel":
		# vrstva popela pod poleny = plocha deska (Misa 0.52 dvakrat): neviditelna, polena lezi na kamennem lozi krbu
		var sp := StandardMaterial3D.new()
		sp.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		sp.albedo_color = Color(0, 0, 0, 0)
		_mats[base] = sp
		return sp
	if base == "uhli":
		var su := StandardMaterial3D.new()
		su.albedo_color = Color(0.05, 0.04, 0.035)
		su.emission_enabled = true
		su.emission = Color(1.0, 0.35, 0.08)
		su.emission_energy_multiplier = 0.6             # doutnajici uhliky
		su.roughness = 0.9
		_mats[base] = su
		return su
	match String(d.get("type", "")):
		"zdivo":
			var s := ShaderMaterial.new()
			s.shader = load("res://shaders/zdivo.gdshader")
			var om: String = d["omitka"]
			s.set_shader_parameter("kamen_a", _t("zdivo", "diff"))
			s.set_shader_parameter("kamen_n", _t("zdivo", "nor"))
			s.set_shader_parameter("kamen_r", _t("zdivo", "rough"))
			s.set_shader_parameter("kamen_h", _t("zdivo", "disp"))
			s.set_shader_parameter("omitka_a", _t(om, "diff"))
			s.set_shader_parameter("omitka_n", _t(om, "nor"))
			s.set_shader_parameter("omitka_r", _t(om, "rough"))
			s.set_shader_parameter("kamen_m", _size("zdivo"))
			s.set_shader_parameter("omitka_m", _size(om))
			s.set_shader_parameter("kryti", float(d["kryti"]))
			s.set_shader_parameter("tint", _v3(d["tint"]))
			s.set_shader_parameter("kamen_tint", _v3(d["kamen"]))
			s.set_shader_parameter("spina", float(d["spina"]))
			s.set_shader_parameter("sum", sum)
			m = s
		"tex":
			var s2 := ShaderMaterial.new()
			s2.shader = load("res://shaders/textura.gdshader")
			var tx: String = d["tex"]
			s2.set_shader_parameter("tex_a", _t(tx, "diff"))
			s2.set_shader_parameter("tex_n", _t(tx, "nor"))
			s2.set_shader_parameter("tex_r", _t(tx, "rough"))
			s2.set_shader_parameter("velikost", _size(tx))
			s2.set_shader_parameter("prohodit", bool(d["swap"]))
			s2.set_shader_parameter("svet", String(d["coord"]) == "world")
			s2.set_shader_parameter("tint", _v3(d["tint"]))
			s2.set_shader_parameter("sedost", float(d.get("grey", 0.0)))
			if d.has("tint2"):
				s2.set_shader_parameter("tint2", _v3(d["tint2"]))
				s2.set_shader_parameter("pestrost", 1.0)
			if tx in ["skala_piskovec", "kamen_lisejnik", "kamen"]:
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("antitile", 1.0)
				s2.set_shader_parameter("skvrny", 1.0)
			if tx == "sindel":
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("skvrny", 1.0)
				s2.set_shader_parameter("radky", 1.0)
			if tx in ["tram", "prkna_ven", "okenice", "omitka_bila", "malta", "dosky", "drevo_stare", "kura"] and String(base) not in ["dub", "deska", "prkna"]:
				s2.set_shader_parameter("sum", sum)
				s2.set_shader_parameter("stekance", 0.55 if String(base).begins_with("roubeni") or String(base) in ["lata", "dub_ven", "sindel_hra"] else 0.4)
				s2.set_shader_parameter("skvrny", 0.6)
			if bool(d["swap"]) and String(d["coord"]) == "uv":
				s2.set_shader_parameter("kus", 1.0)
			if HLOUBKA.has(tx) and (String(d["coord"]) == "world" or tx in ["sindel", "skala_piskovec"]):
				s2.set_shader_parameter("tex_h", _t(tx, "disp"))
				s2.set_shader_parameter("hloubka", HLOUBKA[tx])
			m = s2
		"zem":
			var s3 := ShaderMaterial.new()
			s3.shader = load("res://shaders/zem.gdshader")
			# cesty, dvory, pesiny: udusana hlina bez sterku (fotka "hlina" ma bile oblazky a listi - na tabletu sterk,
			# hlaseni 0.54 bod 3); tmavsi nez louka
			s3.set_shader_parameter("hlina_a", _t("pesina", "diff"))
			s3.set_shader_parameter("hlina_n", _t("pesina", "nor"))
			s3.set_shader_parameter("louka_a", _t("louka", "diff"))
			s3.set_shader_parameter("louka_n", _t("louka", "nor"))
			s3.set_shader_parameter("zrno", load("res://obrazky/zrno_travy.png"))
			s3.set_shader_parameter("letecky_a", _t("louka_letecky", "diff"))
			s3.set_shader_parameter("louka_dal_a", _t("louka_dal", "diff"))
			s3.set_shader_parameter("louka_dal_m", _size("louka_dal"))
			s3.set_shader_parameter("obili_a", _t("pole_obili", "diff"))
			s3.set_shader_parameter("oranice_a", _t("pole_oranice", "diff"))
			s3.set_shader_parameter("obili_m", _size("pole_obili"))
			# kalibrace odrazivosti: fotka * (skutecna odrazivost povrchu / prumer fotky), viz tools/albedo_textur.py
			for u: Array in [["hlina_k", "pesina", 0.05], 
					["obili_k", "pole_obili", 0.20], ["oranice_k", "pole_oranice", 0.10]]:
				s3.set_shader_parameter(u[0], u[2] / maxf(float(_albedo().get(u[1], u[2])), 0.01))
			# louka: barva podkladu = prumer atlasu travy po kanalech -> hrana trsu zmizi
			var at: Array = _albedo().get("atlas_travy_rgb", [0.1, 0.125, 0.025])
			# barva louky z dalky = louka, jak ji hrac vidi vykreslenou (trsy nasvicene shora a s prosvitem, sRGB ~85,118,36),
			# ne prumer atlasu (89,99,44 = olivove hneda - "dalka hneda/seda", hlaseni 0.55 bod 6); overuje test dalka
			s3.set_shader_parameter("barva_louky", BARVA_LOUKY)
			s3.set_shader_parameter("barva_lesa", BARVA_LESA)
			for u2: Array in [["louka_k", "louka"], ["louka_dal_k", "louka_dal"]]:
				var fr: Array = _albedo().get(String(u2[1]) + "_rgb", at)
				# x 1,1 (driv 0,8; 1,3 = svetle zlute plochy u pesin na tabletu, 0.57): teren louky jako osvetleny list, jinak je mezera mezi trsy tmava dira
				# (radce 09:05 bod 2, test dira)
				s3.set_shader_parameter(u2[0], Vector3(float(at[0]) / float(fr[0]), float(at[1]) / float(fr[1]), float(at[2]) / float(fr[2])) * 1.1)
			s3.set_shader_parameter("oranice_m", _size("pole_oranice"))
			s3.set_shader_parameter("hlina_m", _size("pesina"))
			s3.set_shader_parameter("louka_m", _size("louka"))
			s3.set_shader_parameter("letecky_m", _size("louka_letecky"))
			s3.set_shader_parameter("sum", sum)
			m = s3
		"rybnik":
			# rybnik (okrehek, mirne kalny) a potok (tekouci, cisty - dno videt)
			var s4 := ShaderMaterial.new()
			s4.shader = load("res://shaders/voda.gdshader")
			s4.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
			s4.set_shader_parameter("sum", sum)
			var tek := float(d.get("tekouci", 0.0))
			s4.set_shader_parameter("tekouci", tek)
			s4.set_shader_parameter("okrehek", 0.0 if tek > 0.5 else 1.0)
			s4.set_shader_parameter("kalnost", 0.35 if tek > 0.5 else 0.82)
			s4.set_shader_parameter("zakal", Color(0.1, 0.11, 0.07) if tek > 0.5 else Color(0.13, 0.16, 0.10))
			if tek < 0.5:
				s4.set_shader_parameter("deep", Color(0.08, 0.115, 0.08))         # zelenohneda, ne cerna (radce 16:40 bod 2)
			s4.set_shader_parameter("hloubka_vrcholu", tek < 0.5)
			vodni.append(s4)
			m = s4
		"malba":
			var s5 := ShaderMaterial.new()
			s5.shader = load("res://shaders/malba.gdshader")
			s5.set_shader_parameter("zaklad", _v3(d["zaklad"]))
			s5.set_shader_parameter("barva", _v3(d["barva"]))
			s5.set_shader_parameter("sum", sum)
			m = s5
		"sklo":
			var s6 := ShaderMaterial.new()
			s6.shader = load("res://shaders/sklo.gdshader")
			s6.set_shader_parameter("terce", bool(d.get("terce", false)))
			m = s6
		"trava":
			var g := StandardMaterial3D.new()
			g.albedo_color = Color(_v3(d["col"]).x, _v3(d["col"]).y, _v3(d["col"]).z)
			g.vertex_color_use_as_albedo = false
			g.cull_mode = BaseMaterial3D.CULL_DISABLED
			g.roughness = 0.75
			g.backlight_enabled = true
			g.backlight = Color(0.25, 0.3, 0.1)
			m = g
		"voda":
			# prikop: stejna hladina jako rybnik (posouvane vlnky) a kruhove vlnky z life.gd
			var w := ShaderMaterial.new()
			w.shader = load("res://shaders/voda.gdshader")
			w.set_shader_parameter("nmap", load("res://obrazky/voda_normaly.png"))
			w.set_shader_parameter("sum", sum)
			# zelenohneda (radce 16:40 bod 2: 0,10/0,14/0,10), zakal svetlejsi u brehu
			w.set_shader_parameter("deep", Color(0.08, 0.115, 0.08))
			w.set_shader_parameter("zakal", Color(0.13, 0.16, 0.11))
			w.set_shader_parameter("kalnost", 0.82)
			w.set_shader_parameter("hloubka_vrcholu", true)
			vodni.append(w)
			water_mat = w
			m = w
		_:
			var sm := StandardMaterial3D.new()
			var c: Array = d.get("col", [0.5, 0.48, 0.45])
			sm.albedo_color = Color(c[0], c[1], c[2])
			sm.roughness = float(d.get("rough", 0.8))
			sm.metallic = float(d.get("metal", 0.0))
			if d.has("emit"):
				sm.emission_enabled = true
				sm.emission = Color(c[0], c[1], c[2])
				sm.emission_energy_multiplier = minf(float(d["emit"]), 4.0)
			m = sm
	_mats[base] = m
	return m


func _v3(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))


func _apply_materials(mi: MeshInstance3D) -> void:
	var mesh := mi.mesh
	if mesh == null:
		return
	for i in mesh.get_surface_count():
		var old := mesh.surface_get_material(i)
		var nm := old.resource_name if old else ""
		if nm != "":
			var mt := material(nm)
			mi.set_surface_override_material(i, mt)
			if vodni.has(mt):
				_hladina(mi, i)


## Hladina jako oblast (jen pro dotaz "je tu voda a v jake vysce"), ne kolize; male nadoby vynechat.
func _hladina(mi: MeshInstance3D, i: int) -> void:
	var arr := mi.mesh.surface_get_arrays(i)
	var am := ArrayMesh.new()
	am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
	var bb := am.get_aabb()
	if maxf(bb.size.x, bb.size.z) < 3.0:
		return
	var ar := Area3D.new()
	ar.collision_layer = VRSTVA_VODA
	ar.collision_mask = 0
	ar.monitoring = false
	var cs := CollisionShape3D.new()
	cs.shape = am.create_trimesh_shape()
	ar.add_child(cs)
	mi.add_child(ar)


# ------------------------------------------------------------------ kolize

## Potok z Waterways (tools/reka_bake.gd): sit s hloubkou ve vrcholech, mapy proudeni a peny, shader pro Compatibility.
func _reka(parent: Node3D) -> void:
	if not FileAccess.file_exists("res://modely/reka/reka.res"):
		return
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://modely/reka/reka.json"))
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/reka.gdshader")
	m.set_shader_parameter("normal_bump_texture", load("res://modely/reka/water1_normal_bump.png"))
	m.set_shader_parameter("i_texture_foam_noise", load("res://modely/reka/foam_noise.png"))
	m.set_shader_parameter("i_flowmap", load("res://modely/reka/reka_flow.png"))
	m.set_shader_parameter("i_distmap", load("res://modely/reka/reka_dist.png"))
	m.set_shader_parameter("i_valid_flowmap", true)
	m.set_shader_parameter("i_uv2_sides", int(meta["uv2_sides"]))
	m.set_shader_parameter("flow_speed", 0.3)
	m.set_shader_parameter("normal_scale", 0.6)
	m.set_shader_parameter("roughness", 0.15)
	m.set_shader_parameter("foam_amount", 1.2)
	m.set_shader_parameter("foam_color", Color(0.7, 0.72, 0.66, 0.6))
	# barvy v linearnim prostoru (source_color): melka hnedozelena, hluboka tmava; tablet bez HDR = tmavsi nez navrh
	m.set_shader_parameter("melka", Color(0.24, 0.27, 0.15))
	m.set_shader_parameter("hluboka", Color(0.06, 0.08, 0.05))
	m.set_shader_parameter("hloubka_barvy", 1.4)
	m.set_shader_parameter("cirost", 0.55)                # mela voda pruhledna: dno s oblazky a kameny videt
	var mi := MeshInstance3D.new()
	mi.name = "Potok"
	mi.mesh = load("res://modely/reka/reka.res")
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mi)
	reka_mat = m


## Koryto potoka (radce 04:55 bod 4): hladina z osy, teren pod ni vyhloubeny (scripts/koryto.gd) - site terenu
## i mrizka vysek louky (rostliny, trava), pred kolizemi. Stejne koryto pouziva tools/reka_bake.gd pro vodu.
var koryto: RefCounted
var reka_mat: ShaderMaterial         # potok: kameny v toku (kam[]) nastavuje kameny_toku_k()
var kameny_toku: Array = []          # [Vector4(x, z, polomer, uhel proudu)] - kameny ve vode (_krajina)


## 12 nejblizsich kamenu v toku k bodu q do shaderu potoka (cereni a pena kolem kamenu, 0.60 FRONTA voda).
func kameny_toku_k(q: Vector2) -> void:
	if reka_mat == null or kameny_toku.is_empty():
		return
	var kand: Array = []
	for v: Vector4 in kameny_toku:
		var d := Vector2(v.x, v.y).distance_squared_to(q)
		if d < 3600.0:
			kand.append([d, v])
	kand.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var arr: Array = []
	for i in 12:
		arr.append(kand[i][1] if i < kand.size() else Vector4(0, 0, 0, 0))
	reka_mat.set_shader_parameter("kam", arr)
var nadrz: RefCounted
var _tvrz_root: Node3D
var _vys_sit := {}                    # okoli tvrze: vyska z vrcholu siti terenu (mrizka louky val a prikop nezna)


## Hladina prikopu pod padacim mostem (Misa 0.62: "pod mostem tvrze neni voda"): sit Prikop_voda z Blenderu ma
## pod mostem diru ~5 x 7 m (x -2,5..2,5, z 19..26) -> bez hladiny se tam ani nekopalo dno (nadrz kope jen pod
## hladinou) a pod mostem zustal suchy breh. Diru najit podel osy (od x 0 do stran) a zaplatit mrizkou 0,5 m.
func _prikop_zaplata(root: Node3D) -> void:
	var mi := root.find_child("Prikop_voda", true, false) as MeshInstance3D
	if mi == null or not (mi.mesh is ArrayMesh):
		return
	var am := mi.mesh as ArrayMesh
	var si := -1
	for i in am.get_surface_count():
		var mt := am.surface_get_material(i)
		if mt and String(mt.resource_name).begins_with("voda_prikop"):
			si = i
	if si < 0:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var arr := am.surface_get_arrays(si)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
	var tris: Array = []
	var y := 0.0
	for t in idx.size() / 3:
		var p0 := xf * v[idx[t * 3]]
		var p1 := xf * v[idx[t * 3 + 1]]
		var p2 := xf * v[idx[t * 3 + 2]]
		y = p0.y
		if maxf(maxf(p0.z, p1.z), p2.z) > 12.0 and minf(minf(p0.x, p1.x), p2.x) < 12.0 and maxf(maxf(p0.x, p1.x), p2.x) > -12.0:
			tris.append(PackedVector2Array([Vector2(p0.x, p0.z), Vector2(p1.x, p1.z), Vector2(p2.x, p2.z)]))
	var voda := func(x: float, z: float) -> bool:
		for tri: PackedVector2Array in tris:
			if Geometry2D.is_point_in_polygon(Vector2(x, z), tri):
				return true
		return false
	if voda.call(0.0, 22.5):
		return                                          # dira uz neni (novy export)
	var x0 := 0.0
	var x1 := 0.0
	while x0 > -8.0 and not voda.call(x0, 22.5):
		x0 -= 0.1
	while x1 < 8.0 and not voda.call(x1, 22.5):
		x1 += 0.1
	var z0 := 22.5
	var z1 := 22.5
	while z0 > 14.0 and (voda.call(x0 - 0.3, z0 - 0.1) or voda.call(x1 + 0.3, z0 - 0.1)):
		z0 -= 0.1
	while z1 < 32.0 and (voda.call(x0 - 0.3, z1 + 0.1) or voda.call(x1 + 0.3, z1 + 0.1)):
		z1 += 0.1
	# zaplata o kousek pres okraje (na sev bez mezery), UV jako zbytek site (u = x, v = 1 - z)
	x0 -= 0.05
	x1 += 0.05
	var inv := xf.affine_inverse()
	var nx := maxi(2, ceili((x1 - x0) / 0.5) + 1)
	var nz := maxi(2, ceili((z1 - z0) / 0.5) + 1)
	var col: PackedColorArray = arr[Mesh.ARRAY_COLOR] if arr[Mesh.ARRAY_COLOR] != null else PackedColorArray()
	var uv: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
	var nor: PackedVector3Array = arr[Mesh.ARRAY_NORMAL] if arr[Mesh.ARRAY_NORMAL] != null else PackedVector3Array()
	var tan: PackedFloat32Array = arr[Mesh.ARRAY_TANGENT] if arr[Mesh.ARRAY_TANGENT] != null else PackedFloat32Array()
	var b := v.size()
	for j in nz:
		for i in nx:
			var w := Vector3(lerpf(x0, x1, float(i) / (nx - 1)), y, lerpf(z0, z1, float(j) / (nz - 1)))
			v.append(inv * w)
			if not nor.is_empty():
				nor.append(Vector3.UP)
			if not tan.is_empty():
				tan.append_array(PackedFloat32Array([1.0, 0.0, 0.0, 1.0]))
			if not uv.is_empty():
				uv.append(Vector2(w.x, 1.0 - w.z))
			if not col.is_empty():
				col.append(col[0])
	# stejne natoceni jako zbytek site (shader voda cull_back): znamenko podle prvniho trojuhelniku
	var e1 := v[idx[1]] - v[idx[0]]
	var e2 := v[idx[2]] - v[idx[0]]
	var po := e1.z * e2.x - e1.x * e2.z > 0.0
	for j in nz - 1:
		for i in nx - 1:
			var a0 := b + j * nx + i
			if po:
				idx.append_array(PackedInt32Array([a0, a0 + nx + 1, a0 + 1, a0, a0 + nx, a0 + nx + 1]))
			else:
				idx.append_array(PackedInt32Array([a0, a0 + 1, a0 + nx + 1, a0, a0 + nx + 1, a0 + nx]))
	arr[Mesh.ARRAY_VERTEX] = v
	arr[Mesh.ARRAY_INDEX] = idx
	if not nor.is_empty():
		arr[Mesh.ARRAY_NORMAL] = nor
	if not tan.is_empty():
		arr[Mesh.ARRAY_TANGENT] = tan
	if not uv.is_empty():
		arr[Mesh.ARRAY_TEX_UV] = uv
	if not col.is_empty():
		arr[Mesh.ARRAY_COLOR] = col
	var nove := ArrayMesh.new()
	for s in am.get_surface_count():
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr if s == si else am.surface_get_arrays(s))
		nove.surface_set_material(s, am.surface_get_material(s))
		nove.surface_set_name(s, am.surface_get_name(s))
	mi.mesh = nove
	print("prikop pod mostem: zaplata hladiny x %.1f..%.1f z %.1f..%.1f (%d vrcholu)" % [x0, x1, z0, z1, nx * nz])


## Terasa (radce 11:00): kolmy schod vyskove mapy (7-36 m na jedne rade mrizky, x 60-275, z 750-1365) -> svah 48-58 st.
## s nepravidelnym profilem, zaoblenou hranou a nabehem do suti. Polovina vysky se ubere nahore, polovina nasype dole:
## H' = (min_q(H_q + s d) + max_q(H_q - s d)) / 2 (kuzel ze dna a z temene, s = 2 tan uhlu). Upravi mrizku trava_kraj
## (rostliny, louka, _vyska) i vrcholy siti Teren* (kolize se stavi az potom). Puvodni hrany schodu -> _terasa_hrany.
const TERASA := Rect2(60.0, 750.0, 215.0, 615.0)
var _terasa_hrany: Array = []         # [Vector2 stred hrany, Vector2 smer ven (od steny), vyska temene, vyska paty]
var terasa_maska := PackedByteArray()  # uzly mrizky trava_kraj ve svahu terasy (stanoviste skalni_stena) - louka bez travy
var _terasa_g := Vector4()             # x0, z0, k, nx mrizky masky


## Stanoviste skalni_stena (svah upravene terasy, sklon nad ~40 st.): bez travy a trsu. Cte se i z vlaken louky.
func terasa_svah(x: float, z: float) -> bool:
	if terasa_maska.is_empty():
		return false
	var i := roundi((x - _terasa_g.x) / _terasa_g.z)
	var j := roundi((z - _terasa_g.y) / _terasa_g.z)
	var k := j * int(_terasa_g.w) + i
	return i >= 0 and j >= 0 and k < terasa_maska.size() and terasa_maska[k] != 0


func _terasa_terenu(root: Node3D) -> void:
	var t0 := Time.get_ticks_msec()
	var g: Dictionary = data["trava_kraj"]
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	var kr := float(g["k"])
	var gx0 := float(g["x0"])
	var gz0 := float(g["z0"])
	var i0 := maxi(0, floori((TERASA.position.x - gx0) / kr))
	var i1 := mini(nx - 1, ceili((TERASA.end.x - gx0) / kr))
	var j0 := maxi(0, floori((TERASA.position.y - gz0) / kr))
	var j1 := mini(nz - 1, ceili((TERASA.end.y - gz0) / kr))
	var H := PackedFloat32Array()
	H.resize(nx * nz)
	for j in range(j0, j1 + 1):
		for i in range(i0, i1 + 1):
			H[j * nx + i] = ys.decode_s16((j * nx + i) * 2) / 100.0
	# hrany schodu a uzly do 8 bunek od nich
	const W := 8
	var blizko := {}
	for j in range(j0, j1):
		for i in range(i0, i1):
			for sm in 2:
				var a := H[j * nx + i]
				var b := H[(j + sm) * nx + i + 1 - sm]
				var dh := b - a
				if absf(dh) < 3.0 or absf(dh) / kr < 1.2:
					continue
				var dirv := Vector2(1 - sm, sm) * (-1.0 if dh > 0.0 else 1.0)
				var mid := Vector2(gx0 + i * kr, gz0 + j * kr) + Vector2(1 - sm, sm) * kr * 0.5
				_terasa_hrany.append([mid, dirv, maxf(a, b), minf(a, b)])
				for dj in range(-W, W + 1):
					for di in range(-W, W + 1):
						blizko[Vector2i(i + di, j + dj)] = true
	if _terasa_hrany.is_empty():
		return
	var fn := FastNoiseLite.new()
	fn.seed = 1108
	fn.frequency = 0.08                   # uhel svahu po 10-15 m
	var fn2 := FastNoiseLite.new()
	fn2.seed = 1109
	fn2.frequency = 0.3                   # nepravidelny profil 2-4 m
	var H2 := H.duplicate()
	for c: Vector2i in blizko:
		if c.x < i0 or c.y < j0 or c.x > i1 or c.y > j1:
			continue
		var x := gx0 + c.x * kr
		var z := gz0 + c.y * kr
		var sl := 2.0 * tan(deg_to_rad(53.0 + 5.0 * fn.get_noise_2d(x, z)))
		var hu := H[c.y * nx + c.x]
		var hd := hu
		for dj in range(-W, W + 1):
			var jj := c.y + dj
			if jj < j0 or jj > j1:
				continue
			for di in range(-W, W + 1):
				var ii := c.x + di
				if ii < i0 or ii > i1:
					continue
				var dq := sqrt(float(di * di + dj * dj)) * kr * sl
				var hq := H[jj * nx + ii]
				hu = minf(hu, hq + dq)
				hd = maxf(hd, hq - dq)
		H2[c.y * nx + c.x] = 0.5 * (hu + hd)
	# zaobleni hrany a paty (jeden pruchod 3x3 po zmenenych uzlech) a sum profilu jen ve svahu
	var H3 := H2.duplicate()
	var zmen := 0
	for c: Vector2i in blizko:
		if c.x <= i0 or c.y <= j0 or c.x >= i1 or c.y >= j1:
			continue
		var k0 := c.y * nx + c.x
		if absf(H2[k0] - H[k0]) < 0.05:
			continue
		var sm3 := 0.0
		for dj in range(-1, 2):
			for di in range(-1, 2):
				sm3 += H2[(c.y + dj) * nx + c.x + di]
		var zm := absf(H2[k0] - H[k0])
		H3[k0] = lerpf(H2[k0], sm3 / 9.0, 0.6) + fn2.get_noise_2d(gx0 + c.x * kr, gz0 + c.y * kr) * clampf(zm * 0.25, 0.0, 0.9)
		ys.encode_s16(k0 * 2, clampi(roundi(H3[k0] * 100.0), -32000, 32000))
		zmen += 1
	g["y"] = Marshalls.raw_to_base64(ys)
	_vys = {}
	# maska svahu: uzel, kde je po uprave sklon k sousedum nad tan 40 st.
	terasa_maska.resize(nx * nz)
	terasa_maska.fill(0)
	_terasa_g = Vector4(gx0, gz0, kr, nx)
	var ntm := 0
	for c: Vector2i in blizko:
		if c.x <= i0 or c.y <= j0 or c.x >= i1 or c.y >= j1:
			continue
		var k0 := c.y * nx + c.x
		var gr := maxf(maxf(absf(H3[k0 + 1] - H3[k0 - 1]), absf(H3[k0 + nx] - H3[k0 - nx])) / (2.0 * kr),
				maxf(absf(H3[k0] - H3[k0 - 1]), absf(H3[k0] - H3[k0 - nx])) / kr)
		if gr > 0.84:
			terasa_maska[k0] = 1
			ntm += 1
	# vrcholy siti terenu: posun o zmenu mrizky (bilinearne)
	var dlt := func(x: float, z: float) -> float:
		var fx := (x - gx0) / kr
		var fz := (z - gz0) / kr
		var i := floori(fx)
		var j := floori(fz)
		if i < i0 or j < j0 or i >= i1 or j >= j1:
			return 0.0
		fx -= i
		fz -= j
		var a := H3[j * nx + i] - H[j * nx + i]
		var b := H3[j * nx + i + 1] - H[j * nx + i + 1]
		var c2 := H3[(j + 1) * nx + i] - H[(j + 1) * nx + i]
		var d := H3[(j + 1) * nx + i + 1] - H[(j + 1) * nx + i + 1]
		return lerpf(lerpf(a, b, fx), lerpf(c2, d, fx), fz)
	var nv := 0
	for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen":
			continue
		var am := (mi as MeshInstance3D).mesh as ArrayMesh
		if am == null:
			continue
		var xf := (mi as MeshInstance3D).global_transform
		var inv := xf.affine_inverse()
		var nove := ArrayMesh.new()
		var zm2 := 0
		var povrchy: Array = []
		for sf in am.get_surface_count():
			var arr := am.surface_get_arrays(sf)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var zs := 0
			for vi in v.size():
				var w := xf * v[vi]
				if not TERASA.has_point(Vector2(w.x, w.z)):
					continue
				var dd := dlt.call(w.x, w.z) as float
				if absf(dd) > 0.01:
					w.y += dd
					v[vi] = inv * w
					zs += 1
			if zs > 0:
				arr[Mesh.ARRAY_VERTEX] = v
				arr[Mesh.ARRAY_NORMAL] = null
				arr[Mesh.ARRAY_TANGENT] = null
				var st2 := SurfaceTool.new()
				st2.create_from_arrays(arr)
				st2.generate_normals()
				if arr[Mesh.ARRAY_TEX_UV] != null:
					st2.generate_tangents()
				arr = st2.commit_to_arrays()
			povrchy.append(arr)
			zm2 += zs
		if zm2 == 0:
			continue
		for sf in am.get_surface_count():
			nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, povrchy[sf])
			nove.surface_set_material(sf, am.surface_get_material(sf))
			nove.surface_set_name(sf, am.surface_get_name(sf))
		(mi as MeshInstance3D).mesh = nove
		nv += zm2
	print("terasa: %d hran schodu -> svah, %d uzlu mrizky (svah %d), %d vrcholu terenu, %d ms" % [_terasa_hrany.size(), zmen, ntm, nv, Time.get_ticks_msec() - t0])


func _koryto_terenu(root: Node3D) -> void:
	_tvrz_root = root
	_terasa_terenu(root)
	_prikop_zaplata(root)
	# rybnik a prikop (radce 04:55 bod 5): hladiny se stojatou vodou vetsi nez 5 m
	var hl: Array = []
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var me := (mi as MeshInstance3D).mesh
		if me == null:
			continue
		for i in me.get_surface_count():
			var mt := me.surface_get_material(i)
			var mn := String(mt.resource_name).split(".")[0] if mt else ""
			if mn == "voda_prikop" or mn == "voda":
				var bb := AABB()
				var vv: PackedVector3Array = me.surface_get_arrays(i)[Mesh.ARRAY_VERTEX]
				for q in vv:
					bb = bb.expand(q)
				if bb.size.x > 5.0 and bb.size.z > 5.0:
					hl.append([mi, i])
	var nd: RefCounted = preload("res://scripts/nadrz.gd").new()
	nd.priprav(hl)
	nadrz = nd
	for h: Array in hl:
		nd.hloubka_hladiny(h[0], h[1])
	var k: RefCounted = preload("res://scripts/koryto.gd").new()
	var ma_koryto: bool = k.priprav(_vyska)
	if ma_koryto:
		koryto = k
	var n := 0
	var nn := 0
	if ma_koryto:
		for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
			if String(mi.name) == "Teren_reka" or String(mi.name) == "Teren_most":
				k.pokryj(mi as MeshInstance3D)
	for mi in root.find_children("Teren*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if nm == "Teren_obzor" or nm == "Teren_cesta_kamen":
			continue
		if ma_koryto:
			n += k.vyhloub(mi as MeshInstance3D)
		nn += nd.vyhloub(mi as MeshInstance3D)
	_najezdy_mostu(root)
	# mrizka vysek (2 m) pro rostliny a louku
	var g: Dictionary = data["trava_kraj"]
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	var m := 0
	for j in nz:
		for i in nx:
			var x := float(g["x0"]) + i * float(g["k"])
			var z := float(g["z0"]) + j * float(g["k"])
			var st: float = minf(k.strop(x, z) if ma_koryto else INF, nd.strop(x, z))
			var y0 := ys.decode_s16((j * nx + i) * 2) / 100.0
			var y1 := minf(st, y0)
			y1 = najezd_y(x, z, y1)
			if absf(y1 - y0) > 0.005:
				ys.encode_s16((j * nx + i) * 2, clampi(roundi(y1 * 100.0), -32000, 32000))
				m += 1
	g["y"] = Marshalls.raw_to_base64(ys)
	_vys = {}
	print("koryto potoka: %d vrcholu terenu, rybnik a prikop %d (%d hladin), %d bodu mrizky" % [n, nn, hl.size(), m])


## Diry v terenu podel potoka (test prochod 0.56: u mostu pas 7 x 12 m bez site i kolize - jemna sit mostu konci,
## sousedni maji vyrez): mrizka 1 m v pasu koryta, kde paprsek shora nic netrefi, se zalepi ctverci z vysek mrizky
## (po vyhloubeni). Sit Teren_zaplata dostane material zeme a kolizi jako ostatni teren.
func _zaplaty(root: Node3D) -> void:
	if koryto == null:
		return
	var space := root.get_world_3d().direct_space_state
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hotovo := {}
	var n := 0
	var kr = koryto
	for k in kr.body.size() - 1:
		var a: Vector2 = kr.body[k]
		var b: Vector2 = kr.body[k + 1]
		var dl := a.distance_to(b)
		var nrm := (b - a).normalized().orthogonal()
		for m in int(dl) + 1:
			for o in range(-22, 23):
				var q := a.lerp(b, m / maxf(dl, 0.01)) + nrm * o
				var c := Vector2i(floori(q.x), floori(q.y))
				if hotovo.has(c):
					continue
				hotovo[c] = true
				var x := c.x + 0.5
				var z := c.y + 0.5
				# dira = nic pod paprskem, nebo jen hruba sit zapustena 2,5 m pod jemnou tam, kde jemna konci
				# (test prochod: breh za koncem Teren_most, hrac 2 m pod terenem u steny mostu)
				var dira := false
				for sx: float in [-0.25, 0.25]:
					for sz: float in [-0.25, 0.25]:
						var hh := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x + sx, 300, z + sz), Vector3(x + sx, -200, z + sz)))
						# v korytu proti dnu (strop koryta), ne proti mrizce: hruba sit 2,5 m pod dnem tam, kde jemna konci, byla
						# "dnem" a hladina nad ni visela jako trojuhelnik u brehu (Misa 0.62, test hladina); zaplata ma material
						# zeme s UV a tecnami (sede desky 0.56b byly bez nich)
						dira = dira or hh.is_empty() or ((hh["position"] as Vector3).y < minf(_vyska(x + sx, z + sz), kr.strop(x + sx, z + sz)) - 0.8 \
								and not String((hh["collider"] as Node).name).begins_with("Teren_reka") \
								and not String((hh["collider"] as Node).name).begins_with("Teren_most"))
				if not dira:
					continue
				# bunka 1 m s rezervou 0,25 m (prekryv s okolnim terenem, zadna nova skvira)
				var p0 := Vector2(c.x - 0.25, c.y - 0.25)
				var p1 := Vector2(c.x + 1.25, c.y + 1.25)
				var v00 := Vector3(p0.x, minf(_vyska(p0.x, p0.y), kr.strop(p0.x, p0.y)) - 0.03, p0.y)
				var v10 := Vector3(p1.x, minf(_vyska(p1.x, p0.y), kr.strop(p1.x, p0.y)) - 0.03, p0.y)
				var v01 := Vector3(p0.x, minf(_vyska(p0.x, p1.y), kr.strop(p0.x, p1.y)) - 0.03, p1.y)
				var v11 := Vector3(p1.x, minf(_vyska(p1.x, p1.y), kr.strop(p1.x, p1.y)) - 0.03, p1.y)
				for v: Vector3 in [v00, v11, v10, v00, v01, v11]:
					st.set_color(Color(0, 0.85, 0, 1))
					st.set_uv(Vector2(v.x, v.z))
					st.add_vertex(v)
				n += 1
	if n == 0:
		return
	st.generate_normals()
	st.generate_tangents()                 # bez UV a tecen kreslil zem.gdshader zaplatu sede (normala z mapy = 0)
	var mi := MeshInstance3D.new()
	mi.name = "Teren_zaplata"
	mi.mesh = st.commit()
	mi.material_override = material("zem")
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	root.add_child(mi)
	_trimesh(mi)
	print("zaplaty terenu u potoka: %d bunek 1 m" % n)


## Kuly mostu (Misa 0.62: "podpery konci ve vzduchu"): kuly z modelu stoji na puvodnim terenu, zarez potoka
## (koryto.gd) dno snizil o 1-2 m. Kazdy svisly kul (kus site kury vyssi nez 1 m a 2x vyssi nez siroky) se prodlouzi:
## spodni vrcholy na teren v miste kulu - 0,5 m (zapusteni), UV po delce se protahne umerne (kura se nenatahne).
func _most_kuly(mi: MeshInstance3D) -> void:
	var me := mi.mesh as ArrayMesh
	if me == null:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var inv := xf.affine_inverse()
	var nove := ArrayMesh.new()
	var popis: Array = []
	for si in me.get_surface_count():
		var arr := me.surface_get_arrays(si)
		var mt := me.surface_get_material(si)
		if mt != null and String(mt.resource_name).begins_with("kura") and arr[Mesh.ARRAY_INDEX] != null:
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uv = arr[Mesh.ARRAY_TEX_UV]
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
			# kusy site: trojuhelniky + vrcholy ve stejne poloze (union-find)
			var par: Array = range(v.size())
			var poz := {}
			for k in v.size():
				var key := Vector3i(roundi(v[k].x * 1000.0), roundi(v[k].y * 1000.0), roundi(v[k].z * 1000.0))
				if poz.has(key):
					par[_koren(par, k)] = _koren(par, poz[key])
				else:
					poz[key] = k
			for t in idx.size() / 3:
				var a := _koren(par, idx[t * 3])
				par[_koren(par, idx[t * 3 + 1])] = a
				par[_koren(par, idx[t * 3 + 2])] = a
			var skup := {}
			for k in v.size():
				var r := _koren(par, k)
				if not skup.has(r):
					skup[r] = []
				(skup[r] as Array).append(k)
			for r: int in skup:
				var ks: Array = skup[r]
				var bb := AABB(xf * v[ks[0]], Vector3.ZERO)
				for k: int in ks:
					bb = bb.expand(xf * v[k])
				if bb.size.y < 0.5 or bb.size.y < 2.0 * maxf(bb.size.x, bb.size.z):
					continue
				var s := bb.get_center()
				var zem := INF
				for o: Vector2 in [Vector2.ZERO, Vector2(0.3, 0), Vector2(-0.3, 0), Vector2(0, 0.3), Vector2(0, -0.3)]:
					zem = minf(zem, _teren_y(s.x + o.x, s.z + o.y))
				var y0 := bb.position.y
				var y1 := bb.end.y
				var pata := zem - 0.5
				if pata > y0 - 0.05:
					continue
				for k: int in ks:
					var w := xf * v[k]
					if w.y > y0 + 0.02:
						continue
					if uv != null:
						# protejsi vrchol nahore (stejne misto v pudorysu): UV po delce v pomeru nove delky
						var hor := -1
						var hd := INF
						for k2: int in ks:
							var w2 := xf * v[k2]
							var dd := Vector2(w2.x - w.x, w2.z - w.z).length_squared()
							if w2.y > y1 - 0.02 and dd < hd:
								hd = dd
								hor = k2
						if hor >= 0:
							uv[k] = uv[hor] + (uv[k] - uv[hor]) * (y1 - pata) / maxf(y1 - y0, 0.01)
					v[k] = inv * Vector3(w.x, pata, w.z)
				popis.append("%.1f,%.1f pata %.2f -> %.2f (teren %.2f)" % [s.x, s.z, y0, pata, zem])
			arr[Mesh.ARRAY_VERTEX] = v
			if uv != null:
				arr[Mesh.ARRAY_TEX_UV] = uv
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		nove.surface_set_material(si, mt)
		nove.surface_set_name(si, me.surface_get_name(si))
	if popis.is_empty():
		return
	var ovr: Array = []
	for si in me.get_surface_count():
		ovr.append(mi.get_surface_override_material(si))
	mi.mesh = nove
	for si in ovr.size():
		mi.set_surface_override_material(si, ovr[si])
	print("most: %d kulu do zeme: %s" % [popis.size(), "; ".join(popis)])


func _koren(par: Array, a: int) -> int:
	while int(par[a]) != a:
		par[a] = par[par[a]]
		a = par[a]
	return a


## Teren po zarezu potoka a najezdech mostu (mrizka vysek, dno koryta, najezd).
func _teren_y(x: float, z: float) -> float:
	var y := _vyska(x, z)
	if koryto != null:
		y = minf(y, koryto.strop(x, z))
	return najezd_y(x, z, y)


## Kontrola hladiny potoka (Misa 0.62 bod 5: "trojuhelnik hladiny u brehu"): pod kazdym vrcholem hladiny musi byt dno
## do 1,5 m (paprsek na kolize terenu po zarezu, najezdech a zaplatach). Hloubka z peceni (COLOR.r * 4 m) odlisi tune
## (hluboko i pri peceni) od visici hladiny (pri peceni melko, ted pod ni dira nebo hruba sit). Vypis do logu.
## Hloubka ve vrcholech se zaroven prepocita na skutecne dno (Misa 0.62 bod 1: pod mostem pecene 0,2-0,4 m misto
## 0,6 m = pruhledna voda ve stinu mostu jako suche koryto); visici hladina dostane hloubku 0 (pruhledna, neni videt).
func _kontrola_hladiny(parent: Node3D) -> void:
	var pm := parent.get_node_or_null("Potok") as MeshInstance3D
	if pm == null or pm.mesh == null:
		return
	var t0 := Time.get_ticks_msec()
	var space := parent.get_world_3d().direct_space_state
	var arr := pm.mesh.surface_get_arrays(0)
	var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
	var col = arr[Mesh.ARRAY_COLOR]
	if col == null or (col as PackedColorArray).size() != v.size():
		return
	var cols: PackedColorArray = col
	var hot := {}                        # poloha -> nova hloubka (m), nebo -1 = ponechat pecenou
	var visi: Array = []
	var tune := 0
	var zmen := 0
	var bez_site := 0
	for i in v.size():
		var q := pm.global_transform * v[i]
		var key := Vector3i(roundi(q.x * 20.0), roundi(q.y * 20.0), roundi(q.z * 20.0))
		if not hot.has(key):
			var dep := -1.0
			var pec := cols[i].r * 4.0
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(q + Vector3(0, 3.0, 0), q - Vector3(0, 40.0, 0)))
			if h.is_empty():
				if koryto != null and not koryto.blizko(q.x, q.z).is_empty():
					bez_site += 1                       # konec toku za siti terenu (jen Teren_obzor bez kolize)
					dep = 0.0
			else:
				var hl := q.y - (h["position"] as Vector3).y
				if hl <= 1.5:
					dep = maxf(hl, 0.0)
				elif pec > 1.2:
					tune += 1
					dep = minf(hl, 4.0)
				else:
					visi.append("%.1f,%.1f %.1f m (%s)" % [q.x, q.z, hl, String((h["collider"] as Node).name).trim_suffix("_kolize")])
					dep = 0.0
			hot[key] = dep
		var d: float = hot[key]
		if d >= 0.0 and absf(d - cols[i].r * 4.0) > 0.03:
			cols[i].r = clampf(d, 0.0, 4.0) / 4.0
			zmen += 1
	if zmen > 0:
		arr[Mesh.ARRAY_COLOR] = cols
		var am := ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		pm.mesh = am
	print("hladina potoka: %d vrcholu, dno do 1,5 m chybi pod %d (visici hladina, skryta), mimo sit terenu %d, tune hloubeji %d, hloubka prepoctena u %d (%d ms) %s" % [
			hot.size(), visi.size(), bez_site, tune, zmen, Time.get_ticks_msec() - t0, str(visi.slice(0, 12)) if not visi.is_empty() else ""])


## Most pres potok (Misa 0.53: z dalky blika): mezi prkny mostovky jsou 1,5cm mezery, kterymi z dalky problikava
## svetla voda a teren (aliasing). Pod prkna tmava deska po celem pudorysu prken - mezery jsou pak tmave a stale.
func _most_podlozka(mi: MeshInstance3D) -> void:
	var me := mi.mesh
	for i in me.get_surface_count():
		var mt := me.surface_get_material(i)
		if mt == null or not String(mt.resource_name).begins_with("drevo_plot"):
			continue
		# Misa 0.62: mostovka "ctverecky misto prken" - drevo_stare je fotka vodorovnych prken (13 desek na 1,8 m) a
		# prohozene UV (u v modelu = podel prkna) ji kladlo napric: kazde prkno melo svary po 14 cm. Prkno = jedna deska:
		# fotka tramu (vlakna svisle, po prohozeni podel prkna), po delce se opakuje po 1,2 m (kus: jiny vyrez a odstin)
		var pm := mi.get_surface_override_material(i)
		if pm is ShaderMaterial:
			pm = pm.duplicate()
			pm.set_shader_parameter("tex_a", _t("tram", "diff"))
			pm.set_shader_parameter("tex_n", _t("tram", "nor"))
			pm.set_shader_parameter("tex_r", _t("tram", "rough"))
			pm.set_shader_parameter("velikost", 1.2)
			pm.set_shader_parameter("prohodit", true)
			mi.set_surface_override_material(i, pm)
		var v: PackedVector3Array = me.surface_get_arrays(i)[Mesh.ARRAY_VERTEX]
		var body := PackedVector2Array()
		var y0 := INF
		for q in v:
			body.append(Vector2(q.x, q.z))
			y0 = minf(y0, q.y)
		var hull := Geometry2D.convex_hull(body)
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		st.set_normal(Vector3.UP)
		for k in range(1, hull.size() - 2):
			for p: Vector2 in [hull[0], hull[k], hull[k + 1]]:
				st.add_vertex(Vector3(p.x, y0 + 0.005, p.y))
		var pod := MeshInstance3D.new()
		pod.name = "Most_podlozka"
		pod.mesh = st.commit()
		var sm := StandardMaterial3D.new()
		sm.albedo_color = Color(0.05, 0.04, 0.03)
		sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		sm.roughness = 1.0
		pod.material_override = sm
		pod.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.add_child(pod)
		return


func _trimesh(mi: MeshInstance3D) -> void:
	var body := StaticBody3D.new()
	body.name = String(mi.name) + "_kolize"
	var cs := CollisionShape3D.new()
	var tri := mi.mesh.create_trimesh_shape()
	# oboustranne: modely ze SketchUpu maji cast ploch otocenych (podlaha hostince normalou dolu) - jednostranna
	# kolize hrace shora propustila na teren pod podlahou a zespodu ho drzela (zaseknuti ve dverich a na schodech)
	tri.backface_collision = true
	cs.shape = tri
	body.add_child(cs)
	mi.add_child(body)


## Sit skaly/balvanu pro kolizi a usazeni: skala z LOD1 (_daleko, ~800 troj.), balvan z modelu; jen povrch skaly.
func _skala_sit(key: String) -> Mesh:
	var kind := key.trim_suffix("_0")
	var path := "res://modely/rostliny/%s.glb" % (kind + "_daleko" if kind.begins_with("skala_") else kind)
	if not ResourceLoader.exists(path):
		path = "res://modely/rostliny/%s.glb" % kind
	var ps: PackedScene = load(path)
	if ps == null:
		return null
	var inst := ps.instantiate()
	var me: Mesh = null
	for m in inst.find_children("*", "MeshInstance3D", true, false):
		var mm := (m as MeshInstance3D).mesh
		if mm.get_surface_count() > 0:
			me = mm
			break
	inst.free()
	return me


## Plochy site skaly pro dosednuti rostlin (vsechny: nejvyssi prusecik svisle primky je skutecny povrch shora;
## filtr podle normaly bral i spodky previsu a strom skoncil pod rimsou).
func _horni_plochy(me: Mesh) -> PackedVector3Array:
	return me.get_faces()


## Rostliny nad skalou (export je posadil do vysky vrcholu podle obrysu, u uzke jehly ale vedle ni - visely ve
## vzduchu): svisly paprsek proti hornim plocham skaly; bez zasahu dolu na teren.
func _na_povrch_skal(site: Dictionary, mriz: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var plochy := {}
	var dosedlo := 0
	var dolu := 0
	for key: String in r:
		if site.has(key) or key.begins_with("skala_"):
			continue
		for t: Array in r[key]:
			var q := Vector2(t[3], t[11])
			var y := float(t[7])
			var ter := _vyska(q.x, q.y)
			if y < ter + 1.5:
				continue
			var cc := Vector2i(floori(q.x / 16.0), floori(q.y / 16.0))
			var best := -INF
			var kandidat := false
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for pl: Array in mriz.get(cc + Vector2i(dx, dz), []):
						if q.distance_to(pl[0]) > float(pl[1]):
							continue
						kandidat = true
						var sk: String = pl[4]
						if not plochy.has(sk):
							plochy[sk] = _horni_plochy(site[sk])
						var tr: Array = r[sk][pl[5]]
						var xf := Transform3D(Basis(Vector3(tr[0], tr[4], tr[8]), Vector3(tr[1], tr[5], tr[9]), Vector3(tr[2], tr[6], tr[10])), Vector3(tr[3], tr[7], tr[11]))
						var inv := xf.affine_inverse()
						var o := inv * Vector3(q.x, y + 60.0, q.y)          # shora nad celou skalou (jinak start uvnitr)
						var d := (inv.basis * Vector3.DOWN).normalized()
						var pf: PackedVector3Array = plochy[sk]
						for i in range(0, pf.size(), 3):
							var h: Variant = Geometry3D.ray_intersects_triangle(o, d, pf[i], pf[i + 1], pf[i + 2])
							if h != null:
								best = maxf(best, (xf * (h as Vector3)).y)
			if not kandidat:
				continue
			if best > ter:
				t[7] = best - 0.1
				dosedlo += 1
			else:
				t[7] = ter - 0.05
				dolu += 1
	print("usazeni skal: na povrch skaly %d, bez skaly pod sebou na zem %d" % [dosedlo, dolu])
	_na_zem(site, mriz)
	_na_zem_arg = [site, mriz]


## Vsechny rostliny mimo skaly na teren (radce 11:20, D: teren -> upravy -> usazeni -> rozsev): export je
## rozmistil na teren pred upravami (koryto, srovnani u staveb), stromy pak visely 5-17 m nad zemi nebo byly
## zakopane. Tvrz a ves maji vlastni teren (nadvori, dvory) - tam se nesahá.
var _na_zem_arg: Array = []


func _na_zem(site: Dictionary, mriz: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var n := 0
	for key: String in r:
		if site.has(key) or key.begins_with("skala_"):
			continue
		for t: Array in r[key]:
			var q := Vector2(t[3], t[11])
			# uvnitr hradeb tvrze (nadvori ma vlastni teren); ves a okoli tvrze dosednou na teren jako vse ostatni
			# (radce 13:20: bříza u vsi visela - vyjimka byla polomer, ne stavba)
			# okoli tvrze ma vlastni teren (val, prikop - mrizka louky ho nezna); kameny export dal na cesty a dlazbu,
			# ktere mrizka taky nezna (zakopal by je)
			# nadvori tvrze ma vlastni teren (Nadvori*), za hradbou val a prikop - vyska ze site terenu, ne z mrizky louky
			if absf(q.x + 4.5) < 24.0 and absf(q.y - 0.4) < 19.0:
				continue
			var ter := _vyska(q.x, q.y)
			if Vector2(q.x + 4.0, q.y).length() < 75.0:
				ter = _vyska_sit(q.x, q.y)
				if ter == INF:
					continue
			var y := float(t[7])
			# kameny z exportu lezi i na cestach a dlazbe, ktere mrizka nezna (zakopal by je) - dolu jen tam, kde teren
			# snizilo koryto (zarez potoka 0.55: visely 1-20 m nad svahem, hlaseni z hrani 0.55)
			if key.begins_with("kamen_") and Vector2(q.x - 470.0, q.y - 830.0).length() < 130.0:
				continue                                      # ves: kameny na dlazbe a cestach, ktere mrizka nezna
			if y < ter + 0.25 and y > ter - 1.0:
				continue
			# nad skalou (dosedlo na jeji povrch) nechat
			var na_skale := false
			var cc := Vector2i(floori(q.x / 16.0), floori(q.y / 16.0))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for pl: Array in mriz.get(cc + Vector2i(dx, dz), []):
						if q.distance_to(pl[0]) <= float(pl[1]):
							na_skale = true
			if na_skale:
				continue
			if OS.has_environment("TVRZ_NA_ZEM"):
				var oblast := "tvrz" if Vector2(q.x + 4.0, q.y).length() < 80.0 else ("ves" if q.distance_to(Vector2(470.0, 830.0)) < 130.0 else "jinde")
				var kl := "%s %s %s" % [oblast, key.substr(0, 8), "nad" if y > ter else "pod"]
				_stat[kl] = int(_stat.get(kl, 0)) + 1
			t[7] = ter - 0.05
			n += 1
	print("rostliny na teren (visely nebo zakopane): ", n, " ", _stat)


## Usazeni skal a balvanu (radce 04:55): pata na nejnizsim bodu terenu pod obvodem paty (12 smeru), zapustit 0,4 m.
## Plati pro vsechny LOD (stejny index instance) a pro kvadrove kolize balvanu na stejnem miste.
func _usad_skaly(site: Dictionary) -> Dictionary:
	var r: Dictionary = data["rostliny"]
	var posun := {}                      # Vector2i(x*2, z*2) -> dy
	var n := 0
	var hloubky: Array[float] = []
	var plosiny: Array = []              # [stred xz, polomer, vyska nad patou, dy] - co stoji na skale, jde s ni dolu
	for key: String in site:
		var me: Mesh = site[key]
		var fa := me.get_faces()
		var dno := INF
		for v in fa:
			dno = minf(dno, v.y)
		# obvod paty: nejvzdalenejsi vrchol spodniho metru v kazdem z 12 smeru
		var obvod: Array[float] = []
		obvod.resize(12)
		obvod.fill(0.0)
		for v in fa:
			if v.y > dno + 1.0:
				continue
			var i := posmod(roundi(atan2(v.z, v.x) / TAU * 12.0), 12)
			obvod[i] = maxf(obvod[i], Vector2(v.x, v.z).length())
		var kind := key.trim_suffix("_0")
		var klice := [key]
		for k2: String in [kind + "_daleko_0", kind + "_daleko2_0"]:
			if r.has(k2) and (r[k2] as Array).size() == (r[key] as Array).size():
				klice.append(k2)
		for i in (r[key] as Array).size():
			var t: Array = r[key][i]
			var bs := Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10]))
			var o := Vector3(t[3], t[7], t[11])
			var low := _vyska(o.x, o.z)
			for j in 12:
				if obvod[j] <= 0.0:
					continue
				var a := float(j) / 12.0 * TAU
				var w := o + bs * (Vector3(cos(a), 0.0, sin(a)) * obvod[j] * 0.9)
				low = minf(low, _vyska(w.x, w.z))
			var y := low - 0.4 - (bs * Vector3(0, dno, 0)).y
			var dy := minf(y - o.y, 0.0)          # jen dolu; i neposunuta skala je plosina pro dosednuti rostlin
			# balvan nezakopat cely: nejvys 40 % vysky (vez stoji ve svahu, tam rozhoduje obvod)
			if key.begins_with("balvan_"):
				var vy := (bs * Vector3(0, me.get_aabb().size.y, 0)).y
				dy = maxf(dy, -0.4 * vy)
			if dy < 0.0:
				hloubky.append(-dy)
				n += 1
			for k2: String in klice:
				(r[k2][i] as Array)[7] = float(r[k2][i][7]) + dy
			posun[Vector2i(roundi(o.x * 2.0), roundi(o.z * 2.0))] = dy
			# cela skala (vrchol byva sirsi nez pata): co stoji nad ni, jde dolu s ni
			var ab := me.get_aabb()
			var rmax := maxf(maxf(absf(ab.position.x), absf(ab.end.x)), maxf(absf(ab.position.z), absf(ab.end.z)))
			plosiny.append([Vector2(o.x, o.z), rmax * bs.x.length() + 0.5, o.y + 1.0, dy, key, i])
	# rostliny na vrcholu a rimsach skal (borovice na vezi) posunout se skalou, jinak visi ve vzduchu
	var mriz := {}
	for pl: Array in plosiny:
		var cc := Vector2i(floori((pl[0] as Vector2).x / 16.0), floori((pl[0] as Vector2).y / 16.0))
		if not mriz.has(cc):
			mriz[cc] = []
		mriz[cc].append(pl)
	var nahore := 0
	for key: String in r:
		if site.has(key) or key.begins_with("skala_"):
			continue
		for t: Array in r[key]:
			var q := Vector2(t[3], t[11])
			var cc := Vector2i(floori(q.x / 16.0), floori(q.y / 16.0))
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for pl: Array in mriz.get(cc + Vector2i(dx, dz), []):
						# na skale = nad patou skaly i nad terenem (ve svahu u paty roste na zemi)
						if float(t[7]) > float(pl[2]) and q.distance_to(pl[0]) < float(pl[1]) and float(t[7]) > _vyska(q.x, q.y) + 0.5:
							t[7] = float(t[7]) + float(pl[3])
							nahore += 1
	print("usazeni skal: s nimi posunuto %d rostlin a kamenu" % nahore)
	_na_povrch_skal(site, mriz)
	hloubky.sort()
	if n > 0:
		print("usazeni skal: %d zapusteno, median %.2f m, 90 %% %.2f m, max %.2f m" % [n, hloubky[n / 2], hloubky[n * 9 / 10], hloubky[n - 1]])
	return posun


func _collisions(parent: Node3D) -> void:
	var body := StaticBody3D.new()
	body.name = "Kolize"
	parent.add_child(body)
	_kolize_body = body
	# skaly a balvany: trimesh z LOD1 (radce 04:55) - konvexni obal premostil prurvy mezi vezemi (neviditelne steny)
	var site := {}
	for key: String in data["rostliny"]:
		if (key.begins_with("skala_") or key.begins_with("balvan_")) and not key.contains("_daleko") and key.ends_with("_0"):
			var me := _skala_sit(key)
			if me:
				site[key] = me
	_usad_skaly(site)
	var veze := {}
	var troj := 0
	for key: String in site:
		var tvar := (site[key] as Mesh).create_trimesh_shape()
		troj += (site[key] as Mesh).get_faces().size() / 3
		var bb := (site[key] as Mesh).get_aabb()
		for t: Array in data["rostliny"][key]:
			veze[Vector2i(roundi(float(t[3]) * 2.0), roundi(float(t[11]) * 2.0))] = true
			kolize(tvar, bb, Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11])))
	print("kolize skal: ", site.size(), " druhu, ", troj, " troj. na sadu")
	# mekke rostliny (mech, kapradi, byliny) kolizi nemaji (radce 13:20: mech u tvrze se obchazel jako predmet) -
	# export jim nechal kvadr (u mechu zvetseneho 25-50x i 4 m vysoky)
	var mekke := {}
	for key: String in data["rostliny"]:
		for mk: String in MEKKE:
			if key.begins_with(mk):
				for t: Array in data["rostliny"][key]:
					mekke[Vector2i(floori(float(t[3])), floori(float(t[11])))] = true
	# skryte balvany u tvrze (uzel Skaly, Misa: smazat): jejich kvadry z exportu by zustaly jako neviditelne prekazky
	# (test prochod: tvrz-ves zasekl u (11, 60))
	var skryte := {}
	var sk_mi := parent.find_child("Skaly", true, false) as MeshInstance3D
	if sk_mi and not sk_mi.visible and sk_mi.mesh:
		var sxf := sk_mi.global_transform
		for v: Vector3 in sk_mi.mesh.get_faces():
			var g := sxf * v
			skryte[Vector2i(floori(g.x), floori(g.z))] = true
	var bez := 0
	var bez_sk := 0
	for c: Array in data["kolize"]:
		var kc := Vector2i(roundi(float(c[0]) * 2.0), roundi(float(c[2]) * 2.0))
		if veze.has(kc):
			continue
		if skryte.has(Vector2i(floori(float(c[0])), floori(float(c[2])))) and maxf(absf(c[7]), absf(c[9])) < 3.0:
			bez_sk += 1
			continue
		# kvadr rostliny z exportu (do 2 m) u mekke rostliny do 1 m od stredu (stred kvadru neni pata modelu)
		var u_mekke := false
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				u_mekke = u_mekke or mekke.has(Vector2i(floori(float(c[0])) + dx, floori(float(c[2])) + dz))
		if u_mekke and maxf(absf(c[7]), absf(c[9])) < 2.0:
			bez += 1
			continue
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(absf(c[7]), absf(c[8]), absf(c[9])).max(Vector3(0.02, 0.02, 0.02))
		var rot := Quaternion(c[4], c[5], c[6], c[3]).normalized()
		# zabradli schodu (blender/fort.py rail: kvadr 0,12 x 1,1 x L sklopeny podel ramene): celo sklopeneho kvadru
		# je kolme na rameno, na podeste tedy trci sikmo nad ni ve vysce hrudi a kapsle se o nej zastavila (Misa 0.63,
		# test prochod "schody na ochoz": naraz normala -z na konci zabradli). Misto kvadru hranol se svislymi cely:
		# spodni hrana podel ramene, vyska 1,1 m svisle - konec zabradli je svisla plocha na okraji ramene
		if box.size.x < 0.15 and absf(box.size.y - 1.1) < 0.05 and box.size.z > 1.5 and absf((Basis(rot) * Vector3.BACK).y) > 0.2:
			var bs := Basis(rot)
			var ax := bs * Vector3.BACK * (box.size.z * 0.5)
			var dn := bs * Vector3.UP * (box.size.y * 0.5)
			var sx := bs * Vector3.RIGHT * (box.size.x * 0.5)
			var cp := Vector3(c[0], c[1], c[2])
			var body_pts := PackedVector3Array()
			for e: Vector3 in [cp - ax - dn, cp + ax - dn]:
				for sd: float in [-1.0, 1.0]:
					body_pts.append(e + sx * sd)
					body_pts.append(e + sx * sd + Vector3.UP * box.size.y)
			var cvx := ConvexPolygonShape3D.new()
			cvx.points = body_pts
			cs.shape = cvx
			body.add_child(cs)
			continue
		cs.shape = box
		cs.transform = Transform3D(Basis(rot), Vector3(c[0], c[1], c[2]))
		# rampa schodu (fort.py stairs: deska 0,1 m, osa po hranach stupnu, ~45 st.): horni plocha 5 cm nad hranou
		# = na podeste hrana 7 cm a k tomu 45 st. -> kapsle se o ni zastavila; a deska 0,1 m je tenka - kapsle opreta o
		# jeji spodni hranu se vytlacila DOLU pod ni a propadla na zem (Misa 0.63 "propadl podestou", test "schody na
		# ochoz": z podesty y 3,2 na zem y 0 u z 6,7). Deska 0,6 m dolu, horni plocha po hranach stupnu.
		if absf(box.size.y - 0.1) < 0.02 and box.size.z > 2.0 and box.size.x > 0.8 and absf((Basis(rot) * Vector3.BACK).y) > 0.3:
			box.size.y = 0.6
			cs.position -= Basis(rot) * Vector3.UP * 0.35
		body.add_child(cs)
	print("kolize: %d kvadru mekkych rostlin vynechano, %d kvadru skrytych balvanu" % [bez, bez_sk])


## Posledni posazeni na to, co hrac vidi a po cem chodi (radce 20:05 bod 1): paprsek do fyziky sveta (teren, skaly,
## balvany, stavby - kmeny jeste nejsou). Mrizka 2 m se od vzdalene site terenu (Teren_okoli, ridsi) v zarezu potoka
## lisi az o 10 m - to byly stromy a kere visici nad svahem. Visi-li pata vic nez 0,25 m, dosedne (zapusteni zustava);
## co lezi za okrajem terenu (paprsek nic nenajde ani shora), se zahodi.
func _na_povrch(parent: Node3D) -> void:
	var space := parent.get_world_3d().direct_space_state
	var r: Dictionary = data["rostliny"]
	var dolu := 0
	var pryc := 0
	for key: String in r:
		if key.begins_with("skala_"):
			continue
		var zust: Array = []
		for t: Array in r[key]:
			var x := float(t[3])
			var z := float(t[11])
			var y := float(t[7])
			if absf(x + 4.5) < 24.0 and absf(z - 0.4) < 19.0:
				zust.append(t)                                # nadvori tvrze
				continue
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, y + 0.5, z), Vector3(x, y - 80.0, z)))
			if h.is_empty():
				var hu := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(x, y + 120.0, z), Vector3(x, y, z)))
				if hu.is_empty():
					pryc += 1                                 # za okrajem terenu s kolizi (ani pod, ani nad nic)
					continue
				zust.append(t)                                # pod povrchem (zapusteny balvan, kamen v korytu)
				continue
			var hy := float((h["position"] as Vector3).y)
			if y > hy + 0.25:
				var ponor := clampf(_vyska(x, z) - y, 0.05, 1.0)
				t[7] = hy - ponor
				dolu += 1
			zust.append(t)
		r[key] = zust
	print("na povrch (fyzika): dolu %d, za okrajem pryc %d" % [dolu, pryc])


## Impostor ma polohu v pul presnosti (do 6 cm vedle stromu): borovice na hrane skalni veze pak "visela" 4,5 m nad
## zemi pod vezi. Nejvyssi zasah z paprsku v bode a 7 cm kolem.
static func paprsek_imp(space: PhysicsDirectSpaceState3D, pos: Vector3, h: Dictionary) -> Dictionary:
	for o: Vector2 in [Vector2(0.07, 0), Vector2(-0.07, 0), Vector2(0, 0.07), Vector2(0, -0.07)]:
		var p := pos + Vector3(o.x, 0, o.y)
		var h2 := space.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3(0, 0.5, 0), p - Vector3(0, 60, 0)))
		if not h2.is_empty() and (h.is_empty() or (h2["position"] as Vector3).y > (h["position"] as Vector3).y):
			h = h2
	return h


## Dosednuti po prvnim kroku fyziky (main po build): tvary pridane do tela uz ve scene se do prostoru propisi az
## krokem fyziky, _na_povrch je proto nevidel vsechny (skaly skalniho mesta, kvadry) - kamen na skale, mech
## a borovice nad vezi visely 1-1,5 m. Tady stejny paprsek jako hrac/test nad kazdou instanci: visi-li pata
## vic nez 0,25 m, dosedne 5 cm pod povrch.
## Najezdy mostu (Misa 0.60: "most nema napojeni"; "prekresli krajinu"): zarez potoka snizil teren i tam, kam
## mela z mostu navazovat cesta (mostovka 2-5 m nad zemi). Konce mostovky z modelu (hlavni osa vrcholu, most je
## sikmo), teren pred kazdym koncem zvednout k mostovce a do 14 m plynule zpet do puvodniho; v sirce mostovky + 3 m.
## Pred kolizemi a pred mrizkou vysek (trava, rostliny sedi na novem terenu).
const NAJEZD_DELKA := 14.0
var _najezdy: Array = []                  # [konec Vector2, smer ven Vector2, bok Vector2, pul sirky, y mostovky]


func _najezdy_mostu(root: Node3D) -> void:
	var mi := root.find_child("Most_potok", true, false) as MeshInstance3D
	if mi == null or mi.mesh == null:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var body: Array = []
	var ymax := -INF
	var ymin := INF
	for si in mi.mesh.get_surface_count():
		for q: Vector3 in (mi.mesh.surface_get_arrays(si)[Mesh.ARRAY_VERTEX] as PackedVector3Array):
			var w := xf * q
			body.append(w)
			ymax = maxf(ymax, w.y)
			ymin = minf(ymin, w.y)
	if body.is_empty():
		return
	# mostovka: nejcastejsi vyska vrcholu v horni polovine (prkna), po 5 cm
	var hist := {}
	for w: Vector3 in body:
		if w.y > ymin + (ymax - ymin) * 0.35 and w.y < ymax - 0.6:
			var b := roundi(w.y * 20.0)
			hist[b] = int(hist.get(b, 0)) + 1
	var yb := 0
	var nb := -1
	for b: int in hist:
		if int(hist[b]) > nb:
			nb = hist[b]
			yb = b
	var y_most := yb / 20.0 + 0.05
	# hlavni osa v pudorysu (kovariance vrcholu mostovky)
	var c := Vector2.ZERO
	var deck: Array = []
	for w: Vector3 in body:
		if absf(w.y - y_most) < 0.5:
			deck.append(Vector2(w.x, w.z))
			c += Vector2(w.x, w.z)
	c /= maxf(deck.size(), 1)
	var sxx := 0.0
	var szz := 0.0
	var sxz := 0.0
	for p2: Vector2 in deck:
		var d := p2 - c
		sxx += d.x * d.x
		szz += d.y * d.y
		sxz += d.x * d.y
	var uhel := 0.5 * atan2(2.0 * sxz, sxx - szz)
	var osa := Vector2(cos(uhel), sin(uhel))
	var bok := Vector2(-osa.y, osa.x)
	var a0 := INF
	var a1 := -INF
	var b1 := 0.0
	for p2: Vector2 in deck:
		var t := (p2 - c).dot(osa)
		a0 = minf(a0, t)
		a1 = maxf(a1, t)
		b1 = maxf(b1, absf((p2 - c).dot(bok)))
	for e: Array in [[a1, osa], [a0, -osa]]:
		_najezdy.append([c + osa * float(e[0]), e[1], bok, b1, y_most])
	print("most: mostovka y %.2f, osa %s, delka %.1f, pul sirky %.1f" % [y_most, osa, a1 - a0, b1])
	for n in root.find_children("Teren*", "MeshInstance3D", true, false):
		if String(n.name) == "Teren_obzor":
			continue
		_najezd_sit(n as MeshInstance3D)


## Vyska terenu v miste s najezdem mostu (y = puvodni; vraci zvednutou nebo y).
func najezd_y(x: float, z: float, y: float) -> float:
	for nj: Array in _najezdy:
		var d := Vector2(x, z) - (nj[0] as Vector2)
		var al := d.dot(nj[1])
		var lat := absf(d.dot(nj[2]))
		var sir: float = float(nj[3]) + 0.3
		# Misa 0.61: boky najezdu se zvedaly na 3 m = strmina (skala, "klin" pod mostem) -> pozvolny bok 9 m
		if al < -NAJEZD_DELKA or al > NAJEZD_DELKA or lat > sir + 9.0:
			continue
		var cil: float = float(nj[4]) - 0.08                     # tesne pod prkny
		var t := smoothstep(0.0, NAJEZD_DELKA, maxf(al, 0.0))
		var wl := 1.0 - smoothstep(sir, sir + 9.0, lat)
		wl *= wl * (3.0 - 2.0 * wl)
		var ny := lerpf(cil, y, t)
		if al < -1.5:
			# pod koncem mostovky svah naspu 1:1,25 (Misa 0.62: najezd koncil 1,5 m za koncem svislou stenou, pata mostu
			# a kuly visely nad zarezem); do vody (sirka hladiny + 1 m) nikdy - hladina pod mostem souvisla
			ny = cil - (-al - 1.5) * 0.8
			if koryto != null:
				var bl: Array = koryto.blizko(x, z)
				if not bl.is_empty() and float(bl[0]) < float(bl[2]) + 1.0:
					continue
		if ny > y:
			y = lerpf(y, ny, wl)
	return y


func _najezd_sit(mi: MeshInstance3D) -> void:
	var am := mi.mesh as ArrayMesh
	if am == null or _najezdy.is_empty():
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var inv := xf.affine_inverse()
	var nove := ArrayMesh.new()
	var zmen := 0
	for si in am.get_surface_count():
		var arr := am.surface_get_arrays(si)
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		for i in v.size():
			var w := xf * v[i]
			var ny := najezd_y(w.x, w.z, w.y)
			if ny > w.y + 0.01:
				v[i] = inv * Vector3(w.x, ny, w.z)
				zmen += 1
		arr[Mesh.ARRAY_VERTEX] = v
		arr[Mesh.ARRAY_NORMAL] = null
		arr[Mesh.ARRAY_TANGENT] = null
		var st2 := SurfaceTool.new()
		st2.create_from_arrays(arr)
		st2.generate_normals()
		if arr[Mesh.ARRAY_TEX_UV] != null:
			st2.generate_tangents()
		nove.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, st2.commit_to_arrays())
		nove.surface_set_material(si, am.surface_get_material(si))
		nove.surface_set_name(si, am.surface_get_name(si))
	if zmen > 0:
		mi.mesh = nove
		print("  najezd mostu: %s %d vrcholu" % [mi.name, zmen])


func dosednout(parent: Node3D) -> void:
	var rost := parent.find_child("Rostliny", true, false)
	if rost == null:
		return
	var space := parent.get_world_3d().direct_space_state
	var n := 0
	for mmi in rost.find_children("*", "MultiMeshInstance3D", true, false):
		if String(mmi.name).begins_with("skala_"):
			continue
		var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
		if mm == null:
			continue
		var imp := String(mmi.name).begins_with("impostor_")
		var xf := (mmi as Node3D).global_transform
		for i in mm.instance_count:
			var pos: Vector3
			var ti := Transform3D.IDENTITY
			if imp:
				var cd := mm.get_instance_custom_data(i)
				pos = xf.origin + Vector3(cd.r, cd.g, cd.b)
			else:
				ti = mm.get_instance_transform(i)
				pos = xf * ti.origin
			var h := space.intersect_ray(PhysicsRayQueryParameters3D.create(pos + Vector3(0, 0.5, 0), pos - Vector3(0, 60, 0)))
			if imp:
				h = paprsek_imp(space, pos, h)
			if h.is_empty():
				continue
			var dy := (h["position"] as Vector3).y - 0.05 - pos.y
			if dy > -0.25:
				continue
			n += 1
			if imp:
				var cd := mm.get_instance_custom_data(i)
				cd.g += dy
				mm.set_instance_custom_data(i, cd)
			else:
				ti.origin += xf.basis.inverse() * Vector3(0, dy, 0)
				mm.set_instance_transform(i, ti)
	print("dosednuti po fyzice: ", n)


## Mekka rostlina z rozsevu (kere v korytu, u prikopu) na miste maleho kvadru z exportu (kamen, polena): hrac by
## narazil do "kere" (Misa 20:10: krovim projde) - rostlina pryc, kamen zustava.
func _mekke_mimo_kvadry() -> void:
	var kvadry := {}
	for c in _kolize_body.get_children():
		var cs := c as CollisionShape3D
		if cs == null or not (cs.shape is BoxShape3D):
			continue
		var sz: Vector3 = (cs.shape as BoxShape3D).size
		if maxf(sz.x, sz.z) >= 2.0:
			continue
		var key := Vector2i(floori(cs.position.x), floori(cs.position.z))
		if not kvadry.has(key):
			kvadry[key] = []
		(kvadry[key] as Array).append(Vector2(cs.position.x, cs.position.z))
	var pryc := 0
	var r: Dictionary = data["rostliny"]
	for k: String in r:
		var mek := false
		for m: String in MEKKE:
			mek = mek or k.begins_with(m)
		if not mek:
			continue
		var zust: Array = []
		for t: Array in r[k]:
			var pt := Vector2(float(t[3]), float(t[11]))
			var key := Vector2i(floori(pt.x), floori(pt.y))
			var u := false
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for c2: Vector2 in kvadry.get(key + Vector2i(dx, dz), []):
						u = u or c2.distance_to(pt) < 0.6
			if u:
				pryc += 1
			else:
				zust.append(t)
		r[k] = zust
	print("mekke na kvadru pryc: ", pryc)


## Pesina je volna (test prochod: balvan sute pod skalami pres pesinu na Pustou skalu): stromy, balvany, padle kmeny,
## parezy a vetsi kameni do 1,2 m od osy pesiny pryc - kameni na kraji (0,8-1,5 m) a mekke rostliny zustavaji.
func _pesiny_volne() -> void:
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	var smazane := {}
	# skala, kterou osa pesiny neobesla (dve veze tesne u sebe - odsunuti mezi nimi osciluje): pesina ma prednost,
	# skala pryc i se vzdalenymi verzemi (test prochod: tvrz-skaly-hostinec u (-105, 267))
	var skal := 0
	for key: String in r.keys():
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var me := _skala_sit(key)
		if me == null:
			continue
		var rp := maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		var vv := me.get_faces()
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			if pes_d(float(t[3]), float(t[11])) > rp * sc + 1.0:
				continue
			# prekazi jen skala, jejiz sit zasahuje do prujezdu hrace: 0,7 m od osy, 0,3-2 m nad zemi
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11]))
			for i in range(0, vv.size(), 3):
				var g := xf * vv[i]
				if pes_d(g.x, g.z) < 0.7:
					var nad := g.y - _vyska(g.x, g.z)
					if nad > 0.3 and nad < 2.0:
						smazane[Vector2i(roundi(float(t[3]) * 4.0), roundi(float(t[11]) * 4.0))] = true
						break
	for key: String in r.keys():
		if not key.begins_with("skala_"):
			continue
		var zs: Array = []
		for t: Array in r[key]:
			if smazane.has(Vector2i(roundi(float(t[3]) * 4.0), roundi(float(t[11]) * 4.0))):
				skal += 1
			else:
				zs.append(t)
		r[key] = zs
	if skal > 0:
		print("pesiny volne: skal pryc ", skal)
	for key: String in r:
		var tvrde := key.begins_with("balvan_") or key.begins_with("dead_tree") or key.begins_with("tree_stump") \
				or key.begins_with("root_cluster") or _imp_druh(key.substr(0, key.rfind("_"))) != ""
		if not tvrde:
			continue
		# balvan: polomer podle site a meritka (velky balvan 1,5 m od osy pesinu prekryl)
		var rp := 0.0
		if key.begins_with("balvan_") and not key.contains("_daleko"):
			var me := _skala_sit(key.substr(0, key.rfind("_")) + "_0")
			if me:
				rp = maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		var zust: Array = []
		for t: Array in r[key]:
			var q := Vector2(float(t[3]), float(t[11]))
			if pes_d(q.x, q.y) < 1.2 + rp * Vector3(t[0], t[4], t[8]).length():
				pryc += 1
				smazane[Vector2i(roundi(q.x * 4.0), roundi(q.y * 4.0))] = true
				continue
			zust.append(t)
		r[key] = zust
	# kolize odebranych (balvany maji trimesh z _collisions uz pred rozsevem): jinak neviditelna prekazka na pesine
	var kol := 0
	for c in _kolize_body.get_children():
		var cs := c as CollisionShape3D
		if cs and smazane.has(Vector2i(roundi(cs.position.x * 4.0), roundi(cs.position.z * 4.0))):
			cs.queue_free()
			_kolize_body.remove_child(cs)
			kol += 1
	print("pesiny volne: pryc %d, kolizi %d" % [pryc, kol])


## Kmeny stromu (Misa 20:10: "hrac projde krovim, ale stromem, kamenem, skalou ne"): valec do 3 m, prumer podle
## vysky stromu (impostor) a meritka; kere, mlade stromky a vzdalene verze bez kolize.
func _kmeny() -> void:
	var r: Dictionary = data["rostliny"]
	var tvary := {}
	var n := 0
	for key: String in r:
		if key.contains("_daleko") or key.contains("sapling"):
			continue
		var kind := key.substr(0, key.rfind("_"))
		var d := _imp_druh(kind)
		if d == "":
			continue
		var vys := float(_imp_meta[d]["vyska"])
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			var pr := clampf(vys * sc * 0.012, 0.12, 0.6)          # strom 20 m -> kmen 0,48 m prumer
			var q := snappedf(pr, 0.04)
			if not tvary.has(q):
				var cy := CylinderShape3D.new()
				cy.radius = q
				cy.height = 3.0
				tvary[q] = cy
			var xf := Transform3D(Basis(), Vector3(float(t[3]), float(t[7]) + 1.4, float(t[11])))
			if kolize(tvary[q], AABB(Vector3(-q, -1.5, -q), Vector3(2 * q, 3.0, 2 * q)), xf, float(t[7])):
				n += 1
	print("kolize kmenu: ", n)


## Jedine misto, kde vznika kolizni teleso krajiny (radce 20:05 bod 3; Misa 20:10: "hrac projde krovim, ale stromem,
## kamenem, skalou ne - co jde preskocit, to preskoci, ostatni musi obejit, fyzika"). Tvrde veci (skala, balvan, kamen,
## kmen, padly strom) kolizi maji vzdy; mekke (ker, mech, kapradi, trava) nikdy - ty sem nechodi. Jen co vycniva mene
## nez 0,15 m, se vynecha (krok hrace to prekroci stejne, usetri se teleso). bb = AABB tvaru v jeho souradnicich.
const KOLIZE_MIN := 0.15
const MEKKE := ["mech_", "moss_", "kapradi_", "ker_husty", "fern_", "celandine", "periwinkle", "dandelion", "weed_plant", "nettle",
		"shrub_", "sipek", "bez_cerny", "divoka_trava", "grass_", "rakos", "orobinec", "bark_debris", "dry_branches"]


func kolize(tvar: Shape3D, bb: AABB, xf: Transform3D, pata := INF) -> bool:
	var w: AABB = xf * bb
	var o := xf.origin
	var ter := _vyska(o.x, o.z) if pata == INF else pata
	if Vector2(o.x + 4.0, o.z).length() < 80.0:
		ter = minf(ter, _vyska_sit(o.x, o.z))             # val a prikop tvrze: mrizka louky je nezna
	if w.end.y - ter < KOLIZE_MIN:
		return false
	var cs := CollisionShape3D.new()
	cs.shape = tvar
	cs.transform = xf
	_kolize_body.add_child(cs)
	return true


# ------------------------------------------------------------------ informace pro hru

func _info() -> void:
	info["mista"] = data.get("nazvy_mist", [])          # ruiny a jina pojmenovana mista v krajine
	for r: Dictionary in data["mistnosti"]:
		var a: Array = r["ambient"]
		if r.has("yaw"):
			# otocena mistnost (chalupy ve vsi): stred podlahy, rozmery v ramci domu
			var sz: Vector3 = _v3(r["size"])
			var xf := Transform3D(Basis(Vector3.UP, float(r["yaw"])), _v3(r["pos"]))
			info["rooms"].append({"name": r["name"], "title": String(r.get("title", "")), "inv": xf.affine_inverse(), "c": xf.origin,
					"aabb": AABB(Vector3(-sz.x / 2, 0, -sz.z / 2), sz), "ambient": Color(a[0], a[1], a[2])})
			continue
		info["rooms"].append({"name": r["name"], "aabb": AABB(_v3(r["pos"]), _v3(r["size"])),
				"ambient": Color(a[0], a[1], a[2])})
	for fdat: Dictionary in data["ohne"]:
		var d := fdat.duplicate()
		d["pos"] = _v3(fdat["pos"])
		d["night_only"] = false
		info["fires"].append(d)
	for u: Dictionary in data["pouziti"]:
		var d2 := u.duplicate()
		d2["pos"] = _v3(u["pos"])
		info["use"].append(d2)
	for s: Array in data["kour"]:
		info["smoke"].append(_v3(s))


# ------------------------------------------------------------------ rostliny

const NIZKE := ["divoka_trava", "grass_medium_01", "grass_medium_02", "dandelion_01", "nettle_plant", "fern_02",
		"kamen_maly_1", "kamen_maly_2", "kamen_maly_3", "kamen_maly_4", "kamen_maly_5"]
const STREDNI := ["shrub_02", "sipek", "fir_sapling", "rock_moss_set_01", "dry_branches_medium_01", "tree_stump_01",
		"kamen_zula_1", "kamen_zula_2", "kamen_piskovec_1", "kamen_piskovec_2", "kamen_droba_1",
		"orobinec_1", "orobinec_2", "rakos_1", "rakos_2", "bez_cerny_1", "bez_cerny_2", "bez_cerny_3",
		"dead_tree_trunk", "dead_tree_trunk_02", "root_cluster_01", "pine_sapling_small", "tree_stump_02", "balvan_droba_1", "ker_husty"]
## Podrost z druheho chatu (jen zblizka) a dvojice strom / vzdalena verze (prepnuti kolem 60 m).
const PODROST := ["kapradi_1", "kapradi_2", "kapradi_3", "kapradi_les", "kopretiny", "kvety_bile", "byliny", "mech_1", "mech_2", "mech_3", "celandine_01", "periwinkle_plant", "moss_01",
		"bark_debris_01"]
const LOD_M := 220.0
## Stromy zdalky: misto modelu z karet (zdalky ploche "placky") plny nizkopolygonovy tvar stejne velikosti
## (smrk vrstvene kuzely, listnac hrouda koruny); zblizka plny strom. Karty <model>_daleko se uz nepouzivaji.
# 0.61 (les 13-16 FPS na tabletu, overdraw karet listi): plny strom na tabletu jen do 40 m, dal impostor
var STROM_PREP := 40.0 if (OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")) else 60.0
const SKALA_LOD0 := 40.0
const SKALA_LOD1 := 120.0
const STROM_DOHLED := 120.0                # rozpocet: za 120 m zadne stromy (radeji prazdny obzor nez pad)
const LISTNACE := ["lipa", "dub", "briza", "vrba", "buk", "olse", "borovice"]
const TINT_LISTI := {"dub_": Color(0.6, 0.84, 0.58), "briza": Color(0.82, 0.96, 0.72), "smrk": Color(1.3, 1.4, 1.15),
		"borovice": Color(0.9, 1.05, 0.85)}
var _tvary := {}


func _strom_tvar(kind: String) -> String:
	if kind == "smrk" or kind.begins_with("smrk_"):
		return "smrk"
	for l: String in LISTNACE:
		if kind == l or kind.begins_with(l + "_"):
			return l
	return ""


## Plny tvar stromu do obrysu (aabb) puvodniho modelu: barva z vrcholu, dole tmavsi (zdalky objem, ne list papiru).
func _tvar_mesh(druh: String, bb: AABB, listi: Material = null) -> Mesh:
	var key := "%s_%d_%d_%d" % [druh, int(bb.size.y * 10), int(bb.size.x * 10), listi.get_instance_id() if listi else 0]
	if _tvary.has(key):
		return _tvary[key]
	var r := RandomNumberGenerator.new()
	r.seed = hash(key)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	# obal koruny s texturou listi stromu (pruhledne mezery), pod nim tmave jadro - ne hladke jednobarevne koule
	var st2: SurfaceTool = null
	if listi and druh != "smrk":
		st2 = SurfaceTool.new()
		st2.begin(Mesh.PRIMITIVE_TRIANGLES)
	var c := bb.get_center()
	var y0 := bb.position.y
	var h := bb.size.y
	var rad := minf(bb.size.x, bb.size.z) * 0.5
	var kura := Color(0.2, 0.15, 0.1) if druh != "briza" else Color(0.6, 0.58, 0.52)
	var zel: Color = {"smrk": Color(0.07, 0.13, 0.06), "briza": Color(0.2, 0.28, 0.1), "vrba": Color(0.2, 0.26, 0.14),
			"borovice": Color(0.1, 0.16, 0.07),
			"olse": Color(0.11, 0.19, 0.07)}.get(druh, Color(0.14, 0.22, 0.08))
	# kmen
	var kr := maxf(h * 0.012, 0.12)
	_valec(st, Vector3(c.x, y0, c.z), kr, kr * 0.6, h * (0.5 if druh == "smrk" else 0.45), 5, kura, kura)
	if druh == "smrk":
		# patra kuzelu, kazde nize sirsi, zubaty okraj (vetve)
		var pater := 5
		var dole := y0 + h * 0.12
		for i in pater:
			var t0 := float(i) / pater
			var ya := dole + (h - (dole - y0)) * t0 * 0.92
			var yb := ya + (h - (dole - y0)) * 0.34
			if i == pater - 1:
				yb = y0 + h
			var rr := rad * (1.0 - t0 * 0.82) * r.randf_range(0.9, 1.05)
			_kuzel(st, Vector3(c.x, ya, c.z), rr, yb - ya, 9, r, zel * 0.6, zel * 1.15)
	else:
		# koruna: shluk hrud (zploštělé koule s nerovnym povrchem)
		var kz := y0 + h * (0.55 if druh == "borovice" else (0.32 if druh != "vrba" else 0.4))
		var kv := y0 + h - kz
		var n := 5 if rad > 3.0 else 4
		_hruda(st, Vector3(c.x, kz + kv * 0.5, c.z), Vector3(rad * 0.8, kv * 0.5, rad * 0.8), r, zel, st2)
		for i in n:
			var a := TAU * i / n + r.randf() * 0.6
			var d := rad * r.randf_range(0.35, 0.55)
			var p := Vector3(c.x + cos(a) * d, kz + kv * r.randf_range(0.35, 0.65), c.z + sin(a) * d)
			var s := rad * r.randf_range(0.45, 0.6)
			_hruda(st, p, Vector3(s, minf(s, kv * 0.4), s), r, zel * r.randf_range(0.9, 1.1), st2)
	st.generate_normals()
	var mesh := st.commit()
	if st2:
		st2.generate_normals()
		st2.commit(mesh)
		var lm := listi.duplicate() as Material
		if lm is BaseMaterial3D:
			(lm as BaseMaterial3D).cull_mode = BaseMaterial3D.CULL_DISABLED
		mesh.surface_set_material(1, lm)
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 1.0
	mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_LAMBERT_WRAP
	mesh.surface_set_material(0, mat)
	_tvary[key] = mesh
	return mesh


func _valec(st: SurfaceTool, b: Vector3, r0: float, r1: float, h: float, n: int, c0: Color, c1: Color) -> void:
	for i in n:
		var a0 := TAU * i / n
		var a1 := TAU * (i + 1) / n
		var p0 := b + Vector3(cos(a0) * r0, 0, sin(a0) * r0)
		var p1 := b + Vector3(cos(a1) * r0, 0, sin(a1) * r0)
		var q0 := b + Vector3(cos(a0) * r1, h, sin(a0) * r1)
		var q1 := b + Vector3(cos(a1) * r1, h, sin(a1) * r1)
		for v: Array in [[p0, c0], [q0, c1], [q1, c1], [p0, c0], [q1, c1], [p1, c0]]:
			st.set_color(v[1])
			st.add_vertex(v[0])


func _kuzel(st: SurfaceTool, b: Vector3, rr: float, h: float, n: int, r: RandomNumberGenerator, c0: Color, c1: Color) -> void:
	var spic := b + Vector3(0, h, 0)
	var okraj: Array = []
	for i in n * 2:
		# zuby: stridave dal a bliz, konce vetvi lehce dolu
		var a := TAU * i / (n * 2) + r.randf_range(-0.1, 0.1)
		var d := rr * (1.0 if i % 2 == 0 else 0.62) * r.randf_range(0.85, 1.1)
		okraj.append(b + Vector3(cos(a) * d, -h * (0.08 if i % 2 == 0 else 0.0), sin(a) * d))
	var m := okraj.size()
	for i in m:
		var a: Vector3 = okraj[i]
		var bb: Vector3 = okraj[(i + 1) % m]
		for v: Array in [[a, c0], [spic, c1], [bb, c0]]:
			st.set_color(v[1])
			st.add_vertex(v[0])
		# spodek patra (tmavy, zdola nevidet skrz)
		for v: Array in [[a, c0 * 0.5], [bb, c0 * 0.5], [b + Vector3(0, h * 0.2, 0), c0 * 0.4]]:
			st.set_color(v[1])
			st.add_vertex(v[0])


func _hruda(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator, zel: Color, st2: SurfaceTool = null) -> void:
	if st2:
		_obal(st2, cen, sz * 1.12, r)
		sz *= 0.82
	var ny := 4
	var nx := 9
	var body: Array = []
	for j in ny + 1:
		var row: Array = []
		var th := PI * j / ny
		for i in nx:
			var ph := TAU * i / nx
			var k := 1.0 if j == 0 or j == ny else r.randf_range(0.8, 1.15)
			var d := Vector3(sin(th) * cos(ph), cos(th), sin(th) * sin(ph))
			row.append(cen + Vector3(d.x * sz.x, d.y * sz.y, d.z * sz.z) * k)
		body.append(row)
	for j in ny:
		for i in nx:
			var a: Vector3 = body[j][i]
			var b: Vector3 = body[j][(i + 1) % nx]
			var c2: Vector3 = body[j + 1][i]
			var d2: Vector3 = body[j + 1][(i + 1) % nx]
			for v: Vector3 in [a, b, d2, a, d2, c2]:
				# nahore svetlejsi (slunce), dole tmavy stin koruny
				var t := clampf((v.y - cen.y) / sz.y * 0.5 + 0.5, 0.0, 1.0)
				st.set_color(zel * lerpf(0.45, 1.2, t))
				st.add_vertex(v)


var _listi_sh: Shader


func _listi_shader(om: BaseMaterial3D, bb: AABB, strom: bool) -> ShaderMaterial:
	if _listi_sh == null:
		_listi_sh = load("res://shaders/listi.gdshader")
	var m := ShaderMaterial.new()
	m.shader = _listi_sh
	m.resource_name = om.resource_name
	m.set_shader_parameter("barva", om.albedo_texture)
	m.set_shader_parameter("tint", om.albedo_color)
	m.set_shader_parameter("prah", om.alpha_scissor_threshold)
	var c := bb.get_center()
	m.set_shader_parameter("stred", Vector3(c.x, bb.position.y + bb.size.y * (0.62 if strom else 0.5), c.z))
	m.set_shader_parameter("vyska", maxf(bb.end.y, 0.5))
	m.set_shader_parameter("sila_vetru", 1.0 if strom else 0.6)       # kere mene
	m.set_shader_parameter("objem", 0.65 if strom else 0.5)
	return m


func _listi(mesh: Mesh) -> Material:
	# material listi stromu: povrch s pruhlednosti (alfa) - ten se pouzije na obal vzdalene koruny
	for i in mesh.get_surface_count():
		var m := mesh.surface_get_material(i)
		if m is BaseMaterial3D and (m as BaseMaterial3D).transparency != BaseMaterial3D.TRANSPARENCY_DISABLED \
				and (m as BaseMaterial3D).albedo_texture:
			return m
	return null


func _obal(st: SurfaceTool, cen: Vector3, sz: Vector3, r: RandomNumberGenerator) -> void:
	# koule s UV pro texturu listi (opakuje se zhruba po 2,5 m), nerovny povrch
	var ny := 4
	var nx := 9
	var rep := maxf(1.0, maxf(sz.x, sz.y) / 1.25)
	var body: Array = []
	for j in ny + 1:
		var row: Array = []
		var th := PI * j / ny
		for i in nx + 1:
			var ph := TAU * i / nx
			var k := 1.0 if j == 0 or j == ny or i == nx else r.randf_range(0.85, 1.12)
			var d := Vector3(sin(th) * cos(ph), cos(th), sin(th) * sin(ph))
			row.append(cen + Vector3(d.x * sz.x, d.y * sz.y, d.z * sz.z) * k)
		if j > 0 and j < ny:
			row[nx] = row[0]
		body.append(row)
	for j in ny:
		for i in nx:
			var q := [[j, i], [j, i + 1], [j + 1, i + 1], [j, i], [j + 1, i + 1], [j + 1, i]]
			for ij: Array in q:
				st.set_uv(Vector2(float(ij[1]) / nx * rep * 2.0, float(ij[0]) / ny * rep))
				st.add_vertex(body[ij[0]][ij[1]])


const IMP_BUNKA := 256.0
const IMP_DOHLED := 900.0
var _imp_meta := {}


func _imp_druh(kind: String) -> String:
	if _imp_meta.is_empty() and FileAccess.file_exists("res://obrazky/impostory/impostory.json"):
		_imp_meta = JSON.parse_string(FileAccess.get_file_as_string("res://obrazky/impostory/impostory.json"))
	if _imp_meta.has(kind):
		return kind
	for d: String in _imp_meta:
		if kind.begins_with(d) or (d == "vrba" and kind.begins_with("vrba")):
			return d
	return ""


## Impostory: jeden ctverec na strom, MultiMesh po druzich a bunkach 256 m, jednotkove transformace
## (poloha v INSTANCE_CUSTOM), obal bunky rucne (jinak by Godot videl vsechny instance v pocatku).
func _impostory(root: Node3D, imp: Dictionary) -> void:
	var quad := ArrayMesh.new()
	var a := []
	a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-1, 0, 0), Vector3(1, 0, 0), Vector3(1, 2, 0), Vector3(-1, 2, 0)])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	quad.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	var n := 0
	for d: String in imp:
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/impostor.gdshader")
		m.set_shader_parameter("barva", load("res://obrazky/impostory/%s_a.png" % d))
		m.set_shader_parameter("normaly", load("res://obrazky/impostory/%s_n.png" % d))
		var st: Array = _imp_meta[d]["stred"]
		m.set_shader_parameter("stred", Vector3(st[0], st[1], st[2]))
		m.set_shader_parameter("polomer", float(_imp_meta[d]["polomer"]))
		m.set_shader_parameter("fade_od", STROM_PREP - 10.0)
		m.set_shader_parameter("fade_do", IMP_DOHLED)
		for pf: String in TINT_LISTI:
			if d.begins_with(pf):
				m.set_shader_parameter("tint", TINT_LISTI[pf])
		for bc: Vector2i in imp[d]:
			var list: Array = imp[d][bc]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_custom_data = true
			mm.mesh = quad
			mm.instance_count = list.size()
			var lo := Vector3(INF, INF, INF)
			var hi := -lo
			var o := Vector3((bc.x + 0.5) * IMP_BUNKA, 0.0, (bc.y + 0.5) * IMP_BUNKA)     # stred bunky: custom data v pul presnosti
			for i in list.size():
				var c: Color = list[i]
				c = Color(c.r - o.x, c.g, c.b - o.z, c.a)
				mm.set_instance_transform(i, Transform3D.IDENTITY)
				mm.set_instance_custom_data(i, c)
				lo = lo.min(Vector3(c.r, c.g, c.b))
				hi = hi.max(Vector3(c.r, c.g, c.b))
			var r := float(_imp_meta[d]["polomer"]) * 2.5
			mm.custom_aabb = AABB(lo - Vector3(r, r, r), hi - lo + Vector3(r, r, r) * 2.0)
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.material_override = m
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			mmi.name = "impostor_%s_%d_%d" % [d, bc.x, bc.y]
			mmi.position = o
			root.add_child(mmi)
			n += list.size()
	print("impostory: %d stromu" % n)


## Realie 1393 (Misa, radce 09:20): smrk v niznim udoli nerostl. Pod 25 m nad tvrzi (udoli, okoli vsi, louky)
## nahradit smrk dubohabrinou (dub, buk, lipa); na hrebenech, ve skalnim meste a jako primes (15 %) zustava.
func _skala_detail(om: BaseMaterial3D) -> Material:
	var m := ShaderMaterial.new()
	m.resource_name = om.resource_name
	m.shader = load("res://shaders/skala_detail.gdshader")
	m.set_shader_parameter("barva", om.albedo_texture)
	m.set_shader_parameter("normala", om.normal_texture)
	m.set_shader_parameter("detail", _t("skala_piskovec", "diff"))
	m.set_shader_parameter("detail_n", _t("skala_piskovec", "nor"))
	m.set_shader_parameter("detail_m", _size("skala_piskovec"))
	m.set_shader_parameter("detail_prumer", float(_albedo().get("skala_piskovec", 0.2)))   # linearni, jako textura v shaderu
	return m


func _smrky_na_listnace() -> void:
	var r: Dictionary = data["rostliny"]
	var cile := ["dub_stredni_0", "buk_stredni_0", "lipa_stredni_0", "dub_stredni_0"]
	if not cile.all(func(k: String) -> bool: return r.has(k)):
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var n := 0
	for key: String in r.keys():
		if not key.begins_with("smrk_") or key.contains("_daleko"):
			continue
		var zustava: Array = []
		for t: Array in r[key]:
			if float(t[7]) < 25.0 and rng.randf() > 0.15:
				var cil: String = cile[rng.randi() % cile.size()]
				var k := rng.randf_range(0.8, 1.15) / maxf(Vector3(t[0], t[4], t[8]).length(), 0.01)
				var u := t.duplicate()
				for i in [0, 1, 2, 4, 5, 6, 8, 9, 10]:
					u[i] = float(t[i]) * k
				(r[cil] as Array).append(u)
				n += 1
			else:
				zustava.append(t)
		r[key] = zustava
	print("smrky v udoli nahrazeny listnaci: ", n)


var _vys := {}


## Vyska terenu z mrizky louky (trava_kraj: 2 m, cm v int16) - uz pri stavbe, pred fyzikou.
func _vyska(x: float, z: float) -> float:
	if _vys.is_empty():
		for key: String in ["trava_ves", "trava_kraj"]:
			var g: Dictionary = data.get(key, {})
			if g.is_empty():
				continue
			_vys[key] = {"x0": float(g["x0"]), "z0": float(g["z0"]), "k": float(g["k"]), "nx": int(g.get("nx", g.get("n", 0))),
					"nz": int(g.get("nz", g.get("n", 0))), "y": Marshalls.base64_to_raw(String(g["y"]))}
	# ves ma vlastni jemnejsi teren (Teren_ves, mrizka trava_ves); jinde krajina
	for key: String in ["trava_ves", "trava_kraj"]:
		if not _vys.has(key):
			continue
		var g: Dictionary = _vys[key]
		var fx := (x - float(g["x0"])) / float(g["k"])
		var fz := (z - float(g["z0"])) / float(g["k"])
		if key == "trava_ves" and (fx < 1.0 or fz < 1.0 or fx > int(g["nx"]) - 2 or fz > int(g["nz"]) - 2):
			continue
		var i := clampi(floori(fx), 0, int(g["nx"]) - 2)
		var j := clampi(floori(fz), 0, int(g["nz"]) - 2)
		fx = clampf(fx - i, 0.0, 1.0)
		fz = clampf(fz - j, 0.0, 1.0)
		var ys: PackedByteArray = g["y"]
		var nx: int = g["nx"]
		var a := ys.decode_s16((j * nx + i) * 2)
		var b := ys.decode_s16((j * nx + i + 1) * 2)
		var c := ys.decode_s16(((j + 1) * nx + i) * 2)
		var d := ys.decode_s16(((j + 1) * nx + i + 1) * 2)
		return lerpf(lerpf(a, b, fx), lerpf(c, d, fx), fz) / 100.0
	return 0.0


## Nejnizsi teren v okoli (mrizka 2 m na srazu mine skutecny teren o 1-3 m): kmen radeji zapustit nez nechat viset.
func _vyska_min(x: float, z: float, r := 2.0) -> float:
	return minf(minf(_vyska(x, z), minf(_vyska(x + r, z), _vyska(x - r, z))), minf(_vyska(x, z + r), _vyska(x, z - r)))


func _xf(x: float, y: float, z: float, yaw: float, sc: float, nakl := Vector3.ZERO) -> Array:
	var bs := Basis(Vector3.UP, yaw).rotated(Vector3.RIGHT, nakl.x).rotated(Vector3.FORWARD, nakl.z).scaled(Vector3.ONE * sc)
	return [bs.x.x, bs.y.x, bs.z.x, x, bs.x.y, bs.y.y, bs.z.y, y, bs.x.z, bs.y.z, bs.z.z, z]


## Skalni mesto (radce 09:05): vez nestoji na travniku - u paty sut odpadlych bloku zapadana do zeme, mezi nimi
## kapradi, mech a borůvčí (kerik), v okoli borovice, smrk a briza (les mezi vezemi). Pridava do stavajicich druhu.
func _skalni_mesto() -> void:
	var r: Dictionary = data["rostliny"]
	var need := ["balvan_piskovec_2_0", "kamen_piskovec_1_0", "kamen_piskovec_2_0", "kapradi_1_0", "kapradi_2_0", "kapradi_3_0",
			"mech_1_0", "shrub_02_0", "borovice_0", "smrk_0", "briza_0"]
	for k: String in need:
		if not r.has(k):
			return
	var rng := RandomNumberGenerator.new()
	rng.seed = 7313
	var n := 0
	for key: String in r.keys():
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var ps: PackedScene = load("res://modely/rostliny/%s.glb" % key.trim_suffix("_0"))
		if ps == null:
			continue
		var inst := ps.instantiate()
		var bb := AABB()
		for m in inst.find_children("*", "MeshInstance3D", true, false):
			bb = bb.merge((m as MeshInstance3D).get_aabb())
		inst.free()
		var r0 := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			var c := Vector2(t[3], t[11])
			var rad := r0 * sc
			# sut: 5 bloku a kamenu u paty, zapadane 25-40 %
			for q in 5:
				var a := rng.randf() * TAU
				var d := rad * rng.randf_range(0.85, 1.25)
				var p := c + Vector2(cos(a), sin(a)) * d
				var velky := q == 0
				var s2 := rng.randf_range(0.6, 1.1) if velky else rng.randf_range(0.5, 1.4)
				var kind := "balvan_piskovec_2_0" if velky else ("kamen_piskovec_1_0" if rng.randf() < 0.6 else "kamen_piskovec_2_0")
				(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - s2 * rng.randf_range(0.2, 0.4), p.y, rng.randf() * TAU, s2,
						Vector3(rng.randf_range(-0.3, 0.3), 0, rng.randf_range(-0.3, 0.3))))
				n += 1
			# kapradi, mech a kerik mezi sutí
			for q in 7:
				var a := rng.randf() * TAU
				var p := c + Vector2(cos(a), sin(a)) * rad * rng.randf_range(0.9, 1.6)
				var kind: String = ["kapradi_1_0", "kapradi_2_0", "kapradi_3_0", "kapradi_1_0", "mech_1_0", "mech_1_0", "shrub_02_0"][q]
				var s2 := rng.randf_range(0.04, 0.09) if kind.begins_with("mech") else rng.randf_range(0.7, 1.3)
				(r[kind] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, s2))
				n += 1
			# les mezi vezemi: jeden strom u kazde veze (borovice, smrk v chladne souteske, briza na svetline)
			var a := rng.randf() * TAU
			var p := c + Vector2(cos(a), sin(a)) * rad * rng.randf_range(1.6, 2.6)
			var u := rng.randf()
			var kind := "borovice_0" if u < 0.5 else ("smrk_0" if u < 0.8 else "briza_0")
			var ref: Array = (r[kind] as Array)[0]
			var s0 := Vector3(ref[0], ref[4], ref[8]).length()
			(r[kind] as Array).append(_xf(p.x, _vyska_min(p.x, p.y) - 0.15, p.y, rng.randf() * TAU, s0 * rng.randf_range(0.8, 1.2)))
			n += 1
	print("skalni mesto: pridano ", n, " kamenu, rostlin a stromu")


## Les neni park (radce 09:05 C): u stromu parezy, spadle vetve, keriky (lesni patro). Kazdy 5. strom pare nebo
## vetve, kazdy 3. kerik (sipek, ker) v okoli; meritka podle prvni instance druhu (tak jak je model navrzeny).
func _lesni_patro() -> void:
	var r: Dictionary = data["rostliny"]
	var drevo := ["tree_stump_01_0", "tree_stump_02_0", "dry_branches_medium_01_0", "dry_branches_medium_01_1", "dry_branches_medium_01_2"]
	var kere := ["shrub_02_0", "sipek_0"]
	for k: String in drevo + kere:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
	var mer := {}
	for k: String in drevo + kere:
		var t: Array = r[k][0]
		mer[k] = Vector3(t[0], t[4], t[8]).length()
	var rng := RandomNumberGenerator.new()
	rng.seed = 404
	var n := 0
	for key: String in r.keys():
		var lesni := false
		for d: String in ["dub_", "buk_", "lipa_", "smrk_", "borovice_", "olse_", "briza_"]:
			if key.begins_with(d) and not key.contains("_daleko"):
				lesni = true
		if not lesni:
			continue
		var i := 0
		for t: Array in (r[key] as Array).duplicate():
			i += 1
			if i % 5 == 0:
				var k: String = drevo[rng.randi() % drevo.size()]
				var a := rng.randf() * TAU
				var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(2.0, 6.0)
				(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.8, 1.3)))
				n += 1
			if i % 2 == 0:
				var k: String = kere[rng.randi() % kere.size()]
				var a := rng.randf() * TAU
				var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(3.0, 7.0)
				(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.05, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.7, 1.3)))
				n += 1
	print("lesni patro: pridano ", n, " parezu, vetvi a keru")


## Lesni puda (0.63 LES, Misa: "chybi kere, huste lesy"; KCD reference 3-5: kapradi a kere mezi kmeny):
## kolem lesnich stromu v lese (stanoviste) shluky kapradi (3-7 kusu na 1-2 m) a husty nizky ker; ne na pesine.
## Modely z Misova Disku (blender/stromy.py ker_husty, kapradi_les; CC-BY).
func _lesni_puda() -> void:
	var r: Dictionary = data["rostliny"]
	var kap := ["kapradi_les_0", "kapradi_les_1"]
	# Misa 0.63 (Disk Modely/Rostliny): kapradi fern_02 a vlastovicnik (Poly Haven) i do lesa, ne jen ke skalam a hradbam
	for k: String in ["kapradi_1_0", "kapradi_2_0", "kapradi_3_0", "fern_02_0", "fern_02_1", "celandine_01_0", "celandine_01_1"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			kap.append(k)
	for k: String in ["kapradi_les_0", "kapradi_les_1", "ker_husty_0"]:
		if not ResourceLoader.exists(MOD + "rostliny/%s.glb" % k.substr(0, k.rfind("_"))):
			return
		if not r.has(k):
			r[k] = []
	var mer := {}
	for k: String in kap:
		mer[k] = 1.0 if k.begins_with("kapradi_les") else Vector3(r[k][0][0], r[k][0][4], r[k][0][8]).length()
	var rng := RandomNumberGenerator.new()
	rng.seed = 7171
	var nk := 0
	var nb := 0
	var stromy: Array = []
	for key: String in r.keys():
		for d: String in ["dub_", "buk_", "lipa_", "smrk_", "borovice_", "briza_"]:
			if key.begins_with(d) and not key.contains("_daleko"):
				stromy.append(key)
	for key: String in stromy:
		var i := 0
		for t: Array in r[key]:
			i += 1
			var q := Vector2(t[3], t[11])
			if _les(q.x, q.y) < 0.35:
				continue
			# shluk kapradi (u kazdeho druheho stromu), v listnatem lese vic
			if i % 2 == 0:
				var a := rng.randf() * TAU
				var c := q + Vector2(cos(a), sin(a)) * rng.randf_range(1.5, 5.0)
				var k: String = kap[rng.randi() % kap.size()]
				for _j in rng.randi_range(3, 7):
					var p := c + Vector2(rng.randf_range(-1.6, 1.6), rng.randf_range(-1.6, 1.6))
					if pes_d(p.x, p.y) < 1.6 or _u_mostu(p.x, p.y) or not smi_tu_byt(p.x, p.y, k):
						continue
					(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.03, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.7, 1.3)))
					nk += 1
			# husty ker (u kazdeho tretiho), 2-6 m od kmene
			if i % 3 == 1:
				var a := rng.randf() * TAU
				var p := q + Vector2(cos(a), sin(a)) * rng.randf_range(2.0, 6.0)
				if pes_d(p.x, p.y) < 2.2 or _u_mostu(p.x, p.y) or not smi_tu_byt(p.x, p.y, "ker_husty"):
					continue
				(r["ker_husty_0"] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.08, p.y, rng.randf() * TAU, rng.randf_range(0.7, 1.4)))
				nb += 1
	print("lesni puda: kapradi %d, kere %d" % [nk, nb])


## Kvetiny na louce (0.63, Misa: "mely by tam byt i byliny"; bush_daisies z Disku bez slunecnice, blender/kvety.py):
## shluky kopretin a bilych kvetu (5-14 kusu na 1,5 m) po louce mimo les, cesty a vodu; jen zblizka (PODROST).
func _kvetiny_louky() -> void:
	var r: Dictionary = data["rostliny"]
	for k: String in ["kopretiny_0", "kvety_bile_0"]:
		if not ResourceLoader.exists(MOD + "rostliny/%s.glb" % k.trim_suffix("_0")):
			return
		if not r.has(k):
			r[k] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 5150
	var n := 0
	var shluku := int(stan_rect.size.x * stan_rect.size.y / 900.0)
	for _i in shluku:
		var c := stan_rect.position + Vector2(rng.randf(), rng.randf()) * stan_rect.size
		if _louka_m(c.x, c.y) < 0.6 or _les(c.x, c.y) > 0.1 or pes_d(c.x, c.y) < 2.5 or _u_mostu(c.x, c.y):
			continue
		# byliny louky (Misa: "mely by tam byt i byliny"): kopretiny, bile kvety, pampelisky (Disk Rostliny, Poly Haven)
		var w := rng.randf()
		var k := "kopretiny_0" if w < 0.45 else ("kvety_bile_0" if w < 0.7 else "dandelion_01_%d" % (rng.randi() % 5))
		if not r.has(k) or (r[k] as Array).is_empty():
			k = "kopretiny_0"
		# meritko modelu z exportu (pampeliska ma v svet.json sve), nove kvetiny 1
		var sc0 := 1.0 if (r[k] as Array).is_empty() or k.begins_with("kopret") or k.begins_with("kvety") \
				else Vector3(r[k][0][0], r[k][0][4], r[k][0][8]).length()
		for _j in rng.randi_range(5, 14):
			var a := rng.randf() * TAU
			var p := c + Vector2(cos(a), sin(a)) * sqrt(rng.randf()) * 1.5
			if not smi_tu_byt(p.x, p.y, k):
				continue
			(r[k] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.02, p.y, rng.randf() * TAU, sc0 * rng.randf_range(0.8, 1.25)))
			n += 1
	print("kvetiny louky: %d kusu, %d shluku zkuseno" % [n, shluku])


## Byliny (0.64, vetev assets: radce 10:00 BYLINY, pravidla_sveta.json): jitrocel a podbel na kraji pesin (seslapana
## hlina), pelynek na neudrzovane louce (uhor, mez), divizna na vyslunenych strmych strachach; shluky 2-6, jen zblizka.
func _byliny_rozsev() -> void:
	var r: Dictionary = data["rostliny"]
	if not ResourceLoader.exists(MOD + "rostliny/byliny.glb"):
		return
	for i in 4:
		if not r.has("byliny_%d" % i):
			r["byliny_%d" % i] = []
	var rng := RandomNumberGenerator.new()
	rng.seed = 6464
	var n := [0, 0, 0, 0]
	for _i in int(stan_rect.size.x * stan_rect.size.y / 120.0):
		var c := stan_rect.position + Vector2(rng.randf(), rng.randf()) * stan_rect.size
		if _les(c.x, c.y) > 0.3 or _u_mostu(c.x, c.y):
			continue
		var pd := pes_d(c.x, c.y)
		var k := -1
		if pd > 0.7 and pd < 1.8:
			k = 1 if rng.randf() < 0.6 else 3                  # jitrocel / podbel u pesiny
		elif divokost(c.x, c.y) > 0.5 and _louka_m(c.x, c.y) > 0.5 and rng.randf() < 0.25:
			k = 2                                              # pelynek na uhoru
		elif sklon_bunky(c.x, c.y) > 0.35 and sklon_bunky(c.x, c.y) < 1.0 and rng.randf() < 0.5:
			k = 0                                              # divizna na strani
		if k < 0:
			continue
		var key := "byliny_%d" % k
		for _j in rng.randi_range(2, 6):
			var p := c + Vector2(rng.randf_range(-0.8, 0.8), rng.randf_range(-0.8, 0.8))
			if pes_d(p.x, p.y) < 0.6 or not smi_tu_byt(p.x, p.y, key):
				continue
			(r[key] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.02, p.y, rng.randf() * TAU, rng.randf_range(0.75, 1.25)))
			n[k] += 1
	print("byliny: divizna %d, jitrocel %d, pelynek %d, podbel %d" % n)


## Strom ani ker neroste z balvanu (Misa 0.63: strom skrz balvan): pudorysny kruh kazdeho balvanu a kamene
## (meritko x pul sirky modelu) - stromy, mlade stromy a kere uvnitr 85 % polomeru pryc. Mrizka 8 m.
func _stromy_mimo_balvany() -> void:
	var r: Dictionary = data["rostliny"]
	var mriz := {}
	var nb := 0
	for k: String in r.keys():
		if not (k.begins_with("balvan_") or k.begins_with("kamen_zula") or k.begins_with("kamen_piskovec") or k.begins_with("kamen_droba")) \
				or k.contains("_daleko") or (r[k] as Array).is_empty():
			continue
		var sit := _skala_sit(k)
		if sit == null:
			continue
		var bb := sit.get_aabb()
		var pul := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[k]:
			var rad := Vector3(t[0], t[4], t[8]).length() * pul
			if rad < 0.4:
				continue
			var c := Vector2i(floori(float(t[3]) / 8.0), floori(float(t[11]) / 8.0))
			if not mriz.has(c):
				mriz[c] = []
			(mriz[c] as Array).append(Vector3(t[3], t[11], rad))
			nb += 1
	var pryc := 0
	for k: String in r.keys():
		var strom := k.begins_with("shrub") or k.begins_with("sipek") or k.begins_with("bez_") or k.begins_with("ker_husty")
		for pf: String in LISTNACE + JEHLICNATE:
			if k.begins_with(pf):
				strom = true
		if not strom:
			continue
		var zust: Array = []
		for t: Array in r[k]:
			var x := float(t[3])
			var z := float(t[11])
			var c := Vector2i(floori(x / 8.0), floori(z / 8.0))
			var ven := false
			for dj in range(-1, 2):
				for di in range(-1, 2):
					for b: Vector3 in mriz.get(c + Vector2i(di, dj), []):
						if Vector2(x - b.x, z - b.y).length() < b.z * 0.85:
							ven = true
							break
					if ven:
						break
				if ven:
					break
			if not ven:
				zust.append(t)
		pryc += (r[k] as Array).size() - zust.size()
		r[k] = zust
	print("stromy z balvanu pryc: %d (balvanu %d)" % [pryc, nb])


## Hustsi les (0.63, Misa: "chybi kere, huste lesy, cesticky pres les kryte z vrchu stromy"; reference KCD):
## 1) podrost - u kazdeho druheho lesniho stromu mlady strom tehoz druhu (meritko 0,25-0,5, 3-7 m od nej);
## 2) pesiny lesem: kazdych 5-9 m po obou stranach strom 2,2-4,5 m od osy (koruny se nad pesinou sejdou),
##    jehlicnan kde prevazuje jehlicnaty porost. Pote _pesiny_volne (nic do 1,2 m od osy) a _kmeny.
func _les_hustsi() -> void:
	var r: Dictionary = data["rostliny"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 2026
	var listn: Array = []
	var jehl: Array = []
	for k: String in ["buk_stredni_0", "dub_stredni_0", "lipa_stredni_0", "briza_0", "briza_1", "briza_2", "briza_3"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			listn.append(k)
	for k: String in ["smrk_0", "smrk_1", "smrk_2", "borovice_0"]:
		if r.has(k) and not (r[k] as Array).is_empty():
			jehl.append(k)
	if listn.is_empty() or jehl.is_empty():
		return
	var sc_ref := {}
	for k: String in listn + jehl:
		var t: Array = r[k][0]
		sc_ref[k] = Vector3(t[0], t[4], t[8]).length()
	# 1) podrost
	var n_mlade := 0
	for key: String in r.keys():
		if key.contains("_daleko") or not (listn.has(key) or jehl.has(key)):
			continue
		var i := 0
		for t: Array in (r[key] as Array).duplicate():
			i += 1
			if i % 2 != 0 or _les(float(t[3]), float(t[11])) < 0.3:
				continue
			var a := rng.randf() * TAU
			var p := Vector2(t[3], t[11]) + Vector2(cos(a), sin(a)) * rng.randf_range(3.0, 7.0)
			if pes_d(p.x, p.y) < 2.0 or not smi_tu_byt(p.x, p.y, key) or _u_mostu(p.x, p.y):
				continue
			(r[key] as Array).append(_xf(p.x, _vyska(p.x, p.y) - 0.1, p.y, rng.randf() * TAU, float(sc_ref[key]) * rng.randf_range(0.25, 0.5)))
			n_mlade += 1
	# 2) stromoradi podel pesin v lese
	var n_pes := 0
	var osa := pes_osa
	for si in osa.size() - 1:
		var a2 := osa[si]
		var b2 := osa[si + 1]
		if a2 == Vector2.INF or b2 == Vector2.INF:
			continue
		var dl := a2.distance_to(b2)
		var nrm := (b2 - a2).normalized().orthogonal()
		var t2 := rng.randf_range(0.0, 5.0)
		while t2 < dl:
			var o := a2.lerp(b2, t2 / dl)
			t2 += rng.randf_range(5.0, 9.0)
			if _les(o.x, o.y) < 0.25 or absf(o.x + 4.0) < 60.0 and absf(o.y) < 60.0:
				continue
			for sg: float in [1.0, -1.0]:
				var q := o + nrm * sg * rng.randf_range(2.2, 4.5)
				if pes_d(q.x, q.y) < 2.0 or not smi_tu_byt(q.x, q.y, "strom") or _u_mostu(q.x, q.y):
					continue
				var kk: String = (jehl if _st(0, q.x, q.y) > _st(1, q.x, q.y) else listn)[rng.randi() % (jehl.size() if _st(0, q.x, q.y) > _st(1, q.x, q.y) else listn.size())]
				(r[kk] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.1, q.y, rng.randf() * TAU, float(sc_ref[kk]) * rng.randf_range(0.8, 1.2)))
				n_pes += 1
	print("les hustsi: mladych stromu %d, stromu podel pesin %d" % [n_mlade, n_pes])


## Most a najezdy bez stromu a keru (Misa 0.62: "strom roste skrz zabradli" - ker nebo mlady strom z pozdejsiho
## rozsevu, lesni patro, les hustsi): posledni pruchod po vsech rozsevech; most a najezdy (14 m) v sirce mostu + 4 m
## (stromy + 7 m, koruna nad zabradli), vcetne vzdalenych verzi (stejne misto).
func _most_bez_stromu() -> void:
	if _najezdy.size() < 2:
		return
	var a: Vector2 = _najezdy[0][0]
	var b: Vector2 = _najezdy[1][0]
	var c := (a + b) * 0.5
	var osa: Vector2 = _najezdy[0][1]
	var bok: Vector2 = _najezdy[0][2]
	var pul := a.distance_to(b) * 0.5 + NAJEZD_DELKA
	var sir := float(_najezdy[0][3])
	var r: Dictionary = data["rostliny"]
	var pryc := 0
	for key: String in r.keys():
		var kind := key.split("_daleko")[0]
		var strom := _strom_tvar(kind) != "" or kind.begins_with("vrba") or kind.begins_with("olse") or kind.begins_with("borovice") \
				or kind.begins_with("briza") or kind.begins_with("dead_tree")
		var ker := kind.begins_with("shrub") or kind.begins_with("bez_") or kind.begins_with("sipek") or kind.begins_with("liska") \
				or kind.begins_with("ker")
		if not strom and not ker:
			continue
		var okraj := sir + (7.0 if strom else 4.0)
		var zust: Array = []
		for t: Array in r[key]:
			var d := Vector2(float(t[3]), float(t[11])) - c
			if absf(d.dot(osa)) < pul and absf(d.dot(bok)) < okraj:
				pryc += 1
				continue
			zust.append(t)
		r[key] = zust
	print("most: stromu a keru u mostu a najezdu pryc ", pryc)


func _u_mostu(x: float, z: float) -> bool:
	if _tvrz_root == null:
		return false
	var mm := _tvrz_root.find_child("Most_potok", true, false) as MeshInstance3D
	if mm == null:
		return false
	var b := ((mm.global_transform if mm.is_inside_tree() else mm.transform) * mm.get_aabb()).grow(5.0)
	var ve_vode: bool = koryto != null and not koryto.blizko(x, z).is_empty() and float(koryto.blizko(x, z)[0]) < float(koryto.blizko(x, z)[2]) + 0.5
	return ve_vode or (x > b.position.x and x < b.end.x and z > b.position.z and z < b.end.z)


## Tvrz zvenci (radce: prvni dojem): u paty hradeb zarostle - koprivy, vysoka trava, pampelisky (kosa tam
## nedosahne); na brehu prikopu vrby hlavate (orezavane, lidska stopa). Obvod hradeb z exportu: x -27..18, z -16..17.
func _tvrz_zvencí() -> void:
	var r: Dictionary = data["rostliny"]
	for k: String in ["nettle_plant_0", "grass_medium_02_0", "dandelion_01_0", "vrba_hlavata_1_0", "vrba_hlavata_2_0"]:
		if not r.has(k) or (r[k] as Array).is_empty():
			return
	var mer := {}
	for k: String in ["nettle_plant_0", "grass_medium_02_0", "dandelion_01_0", "vrba_hlavata_1_0", "vrba_hlavata_2_0"]:
		var t: Array = r[k][0]
		mer[k] = Vector3(t[0], t[4], t[8]).length()
	var voda := float(data.get("voda_y", -2.75))
	var rng := RandomNumberGenerator.new()
	rng.seed = 1390
	var x0 := -27.4
	var x1 := 18.3
	var z0 := -16.4
	var z1 := 17.2
	var obvod := 2.0 * ((x1 - x0) + (z1 - z0))
	var n := 0
	for i in int(obvod * 3.0):
		var u := rng.randf() * obvod
		var off := 0.3 + pow(rng.randf(), 1.5) * 2.2
		var p: Vector2
		if u < x1 - x0:
			p = Vector2(x0 + u, z0 - off)
		elif u < 2.0 * (x1 - x0):
			p = Vector2(x0 + u - (x1 - x0), z1 + off)
		elif u < 2.0 * (x1 - x0) + (z1 - z0):
			p = Vector2(x0 - off, z0 + u - 2.0 * (x1 - x0))
		else:
			p = Vector2(x1 + off, z0 + u - 2.0 * (x1 - x0) - (z1 - z0))
		if absf(p.x + 3.0) < 2.5 and p.y > z1:
			continue                                    # pred branou a mostem volno
		var y := _vyska(p.x, p.y)
		if y < voda + 0.25:
			continue
		var w := rng.randf()
		var k := "nettle_plant_0" if w < 0.4 else ("grass_medium_02_0" if w < 0.85 else "dandelion_01_0")
		(r[k] as Array).append(_xf(p.x, y - 0.03, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.8, 1.3)))
		n += 1
	# kere a kapradi na valu (Misa 0.63: "val prazdny"): sipek, bez, kapradi ve shlucich, ne pred branou
	for kk: String in ["sipek_0", "bez_cerny_1_0", "bez_cerny_2_0", "kapradi_1_0", "fern_02_0", "kopretiny_0"]:
		if not r.has(kk) or (r[kk] as Array).is_empty():
			continue
		var sc0 := 1.0 if kk.begins_with("kopret") else Vector3(r[kk][0][0], r[kk][0][4], r[kk][0][8]).length()
		var pocet := 9 if kk.begins_with("sipek") or kk.begins_with("bez") else 22
		for _i in pocet:
			var u := rng.randf() * obvod
			var off := 0.6 + rng.randf() * 1.6
			var p: Vector2
			if u < x1 - x0:
				p = Vector2(x0 + u, z0 - off)
			elif u < 2.0 * (x1 - x0):
				p = Vector2(x0 + u - (x1 - x0), z1 + off)
			elif u < 2.0 * (x1 - x0) + (z1 - z0):
				p = Vector2(x0 - off, z0 + u - 2.0 * (x1 - x0))
			else:
				p = Vector2(x1 + off, z0 + u - 2.0 * (x1 - x0) - (z1 - z0))
			if absf(p.x + 1.0) < 5.0 and p.y > z1:
				continue                                # pred branou a mostem volno
			var y := _vyska(p.x, p.y)
			if y < voda + 0.3:
				continue
			var shluk := 1 if kk.begins_with("sipek") or kk.begins_with("bez") else rng.randi_range(2, 5)
			for _j in shluk:
				var q := p + Vector2(rng.randf_range(-0.7, 0.7), rng.randf_range(-0.7, 0.7))
				(r[kk] as Array).append(_xf(q.x, _vyska(q.x, q.y) - 0.04, q.y, rng.randf() * TAU, sc0 * rng.randf_range(0.7, 1.15)))
				n += 1
	# vrby hlavate na brehu prikopu: misto tesne nad hladinou na obvodu 4-12 m za hradbou
	var v := 0
	for i in 400:
		if v >= 14:
			break
		var a := rng.randf() * TAU
		var p := Vector2(-4.5, 0.4) + Vector2(cos(a) * 34.0, sin(a) * 28.0) * rng.randf_range(0.95, 1.25)
		var y := _vyska(p.x, p.y)
		if y < voda + 0.15 or y > voda + 1.2 or (absf(p.x + 3.0) < 6.0 and p.y > 0.0):
			continue
		var k := "vrba_hlavata_1_0" if rng.randf() < 0.5 else "vrba_hlavata_2_0"
		(r[k] as Array).append(_xf(p.x, y - 0.1, p.y, rng.randf() * TAU, float(mer[k]) * rng.randf_range(0.85, 1.15)))
		v += 1
	print("tvrz zvenci: %d rostlin u hradeb, %d vrb u prikopu" % [n, v])


## Maska stanoviste (radce 07:50 bod 1), mrizka louky 2 m: R = krytí korunami jehlicnanu, G = listnacu, B = skaly (pata a
## okoli 12 m), A = pesina. Z ni zem.gdshader vybira povrch (listi / jehlici / pisek s jehlicim / mech / udusana
## pesina) a louka.gd nedava trsy na pesiny. Pocita se z rozmisteni stromu a skal po vsech upravach (_plants).
const JEHLICNATE := ["smrk", "borovice", "fir_", "pine_"]
const PESINY := [                      # pesiny (radce 07:50): tvrz - kostelik, Doubrava, skalni mesto - Pusta skala - hostinec, ves - Doubrava
	[Vector2(2.5, 40.0), Vector2(90.0, 60.0), Vector2(160.0, 35.0), Vector2(220.0, 40.0)],
	[Vector2(10.0, 60.0), Vector2(120.0, 160.0), Vector2(230.0, 260.0), Vector2(300.0, 340.0)],
	[Vector2(-20.0, 50.0), Vector2(-80.0, 180.0), Vector2(-112.0, 290.0), Vector2(-150.0, 420.0), Vector2(-190.0, 540.0),
			Vector2(-150.0, 700.0), Vector2(-95.0, 860.0)],
	# do vsi kolem zapadniho konce horni rady statku na naves (test prochod: rovne pres dvory a ploty)
	[Vector2(300.0, 340.0), Vector2(380.0, 520.0), Vector2(430.0, 700.0), Vector2(432.0, 775.0), Vector2(462.0, 806.0)],
	# od padaciho mostu k rozcesti (Misa 0.62: "pred tvrzi ma byt cesta, ne trava"; pesiny zacinaly 20 m od mostu)
	[Vector2(-3.0, 23.0), Vector2(-1.5, 31.0), Vector2(2.5, 40.0)],
	[Vector2(2.5, 40.0), Vector2(-8.0, 45.0), Vector2(-20.0, 50.0)],
	[Vector2(2.5, 40.0), Vector2(6.0, 50.0), Vector2(10.0, 60.0)],
	# nadvori tvrze (Misa 0.62: "maji tam byt cesticky"): od brany ke studni a ke dverim palace, odbocka ke kovarne a ke stajim
	[Vector2(-3.0, 17.0), Vector2(-2.5, 10.0), Vector2(1.0, 0.0), Vector2(8.0, -6.8)],
	[Vector2(-2.5, 10.0), Vector2(-8.0, 9.0), Vector2(-14.0, 7.0)],
	[Vector2(1.0, 0.0), Vector2(-0.1, -6.8)],
	[Vector2(-2.5, 10.0), Vector2(6.0, 11.0), Vector2(12.0, 12.0)],
]
var stanoviste: Image                  # RGBA8 na mrizce trava_kraj (2 m)
var _st_ch: Array[PackedFloat32Array] = []
var _st_n := Vector2i.ZERO
var _kolize_body: StaticBody3D
var _uvnitr: Array = []
var _stat := {}
var stan_rect := Rect2()


## Osa pesin jako lomena cara (bod po 2 m): zvlnena vlnkou _pes_o a odsunuta od skal (test prochod: pesina na Pustou
## skalu vedla skrz skalni veze) - vsechny pesiny za sebou, mezi pesinami Vector2.INF.
var pes_osa := PackedVector2Array()
var pes_dist: Image                    # vzdalenost od osy pesiny / PES_DMAX (R8, mrizka 0,5 m) - louka, rozsev (shader ma pesinu v stanoviste.a)
const PES_K := 0.5
const PES_DMAX := 4.0


## Kruh pudorysu nesedi na nepravidelnou skalu (masiv se 3 vezemi: test prochod u (-161, 638)): body osy jeste
## odsunout od skutecnych vrcholu a tezist trojuhelniku skal (LOD1) v pasu 0,3-2,2 m nad zemi - na 1,3 m.
func _pes_od_sten() -> void:
	var r: Dictionary = data["rostliny"]
	var body := {}                                   # bunka 16 m -> indexy bodu osy
	for i in pes_osa.size():
		if pes_osa[i] != Vector2.INF:
			var cc := Vector2i(floori(pes_osa[i].x / 16.0), floori(pes_osa[i].y / 16.0))
			if not body.has(cc):
				body[cc] = []
			body[cc].append(i)
	var steny := {}                                  # bunka 2 m -> body sten (xz)
	for key: String in r:
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var me := _skala_sit(key)
		if me == null:
			continue
		var f := me.get_faces()
		var rp := maxf(me.get_aabb().size.x, me.get_aabb().size.z) * 0.5
		for t: Array in r[key]:
			var c := Vector2(float(t[3]), float(t[11]))
			var rr := rp * Vector3(t[0], t[4], t[8]).length() + 3.0
			var blizko := false
			for dx in range(-ceili(rr / 16.0), ceili(rr / 16.0) + 1):
				for dz in range(-ceili(rr / 16.0), ceili(rr / 16.0) + 1):
					blizko = blizko or body.has(Vector2i(floori(c.x / 16.0) + dx, floori(c.y / 16.0) + dz))
			if not blizko:
				continue
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])), Vector3(t[3], t[7], t[11]))
			for i in range(0, f.size(), 3):
				for g: Vector3 in [xf * f[i], xf * f[i + 1], xf * f[i + 2], xf * ((f[i] + f[i + 1] + f[i + 2]) / 3.0)]:
					var nad := g.y - _vyska(g.x, g.z)
					if nad < 0.3 or nad > 2.2:
						continue
					var k2 := Vector2i(floori(g.x / 2.0), floori(g.z / 2.0))
					if not steny.has(k2):
						steny[k2] = []
					steny[k2].append(Vector2(g.x, g.z))
	var posun := 0
	for i in pes_osa.size():
		var p := pes_osa[i]
		if p == Vector2.INF:
			continue
		for it in 4:
			var kk := Vector2i(floori(p.x / 2.0), floori(p.y / 2.0))
			var tlak := Vector2.ZERO
			for dx in range(-1, 2):
				for dz in range(-1, 2):
					for v: Vector2 in steny.get(kk + Vector2i(dx, dz), []):
						var d := p.distance_to(v)
						if d < 1.3:
							tlak += (p - v) / maxf(d, 0.01) * (1.3 - d)
			if tlak == Vector2.ZERO:
				break
			p += tlak.limit_length(1.3)
			posun += 1
		pes_osa[i] = p
	print("pesiny od sten skal: %d posunu" % posun)


func _pes_postav() -> void:
	# skaly: kruhy pudorysu (stred, polomer + 1,5 m)
	var skaly: Array = []
	var r: Dictionary = data["rostliny"]
	for key: String in r:
		if not key.begins_with("skala_") or key.contains("_daleko"):
			continue
		var me := _skala_sit(key)
		if me == null:
			continue
		var bb := me.get_aabb()
		var rp := maxf(bb.size.x, bb.size.z) * 0.5
		for t: Array in r[key]:
			var sc := Vector3(t[0], t[4], t[8]).length()
			skaly.append([Vector2(t[3], t[11]), rp * sc * 0.9 + 2.0])   # test prochod: 0,8 + 1,5 m zachytilo previs hlavy
	# stavby v ceste (test prochod: vez zriceniny na Puste skale, kvadr chalupy ve vsi): staticke stavby a kvadry
	# z exportu od 0,6 m mimo tvrz (tam vede pesina branou)
	skaly.append_array(_stavby)
	for c: Array in data["kolize"]:
		var vel := maxf(absf(c[7]), absf(c[9]))
		if vel < 0.6 or (absf(float(c[0])) < 45.0 and absf(float(c[2])) < 50.0):
			continue
		# dlouhy tenky kvadr (plot 27 m): retez kruhu po delce, ne jeden kruh pres pul vsi
		var bs := Basis(Quaternion(c[4], c[5], c[6], c[3]).normalized())
		var sx := absf(float(c[7]))
		var sz := absf(float(c[9]))
		var osa_k := Vector2(bs.x.x, bs.x.z).normalized() if sx >= sz else Vector2(bs.z.x, bs.z.z).normalized()
		var delka := maxf(sx, sz)
		var tl := minf(sx, sz)
		var kusu := maxi(1, ceili(delka / maxf(tl, 1.0)))
		for i in kusu:
			var u := (i + 0.5) / kusu - 0.5
			skaly.append([Vector2(c[0], c[2]) + osa_k * u * delka, maxf(tl, delka / kusu) * 0.71 + 1.0])
	var mriz := {}
	for i in skaly.size():
		var c: Vector2 = skaly[i][0]
		var rr := float(skaly[i][1]) - 16.0                  # sousedni bunky pokryji 16 m, vetsi kruh i do dalsich
		var e := maxi(0, ceili(rr / 16.0))
		for ex in range(-e, e + 1):
			for ez in range(-e, e + 1):
				var cc := Vector2i(floori(c.x / 16.0) + ex, floori(c.y / 16.0) + ez)
				if not mriz.has(cc):
					mriz[cc] = []
				mriz[cc].append(i)
	var sg := pes_useky()
	pes_osa = PackedVector2Array()
	var predchozi := -1
	for si in sg.size():
		var a := Vector2(sg[si].x, sg[si].y)
		var b := Vector2(sg[si].z, sg[si].w)
		if predchozi >= 0 and pes_osa[pes_osa.size() - 1].distance_to(a) > 0.5:
			pes_osa.append(Vector2.INF)                       # nova pesina
		var dl := a.distance_to(b)
		var dr := (b - a) / dl
		var n := int(dl / 2.0)
		for m in n + 1:
			var x := dl * m / n
			var p := a + dr * x + dr.orthogonal() * _pes_o(x, dl, si)
			# odsunout od skal (3 pruchody - mezi dvema vezemi zustane uprostred)
			for it in 3:
				var cc := Vector2i(floori(p.x / 16.0), floori(p.y / 16.0))
				for dx in range(-1, 2):
					for dz in range(-1, 2):
						for i: int in mriz.get(cc + Vector2i(dx, dz), []):
							var c: Vector2 = skaly[i][0]
							var rr: float = skaly[i][1]
							var d := p.distance_to(c)
							if d < rr:
								p = c + (p - c) / maxf(d, 0.01) * rr
			if m == 0 and predchozi >= 0 and pes_osa[pes_osa.size() - 1] != Vector2.INF:
				continue                                      # navazny bod useku je uz v ose
			pes_osa.append(p)
		predchozi = si
	# vyhladit (odsunute body by delaly zuby) - klouzavy prumer 5 bodu, konce pesin drzi
	var hl := pes_osa.duplicate()
	for i in range(2, pes_osa.size() - 2):
		var ok := true
		var sm := Vector2.ZERO
		for j in range(i - 2, i + 3):
			if pes_osa[j] == Vector2.INF:
				ok = false
			else:
				sm += pes_osa[j]
		if ok:
			hl[i] = sm / 5.0
	# po vyhlazeni jeste jednou od skal (prumer vrati bod mezi dvema odsunutymi zpet ke skale)
	for i in hl.size():
		var p := hl[i]
		if p == Vector2.INF:
			continue
		var cc := Vector2i(floori(p.x / 16.0), floori(p.y / 16.0))
		for dx in range(-1, 2):
			for dz in range(-1, 2):
				for k: int in mriz.get(cc + Vector2i(dx, dz), []):
					var c: Vector2 = skaly[k][0]
					var d := p.distance_to(c)
					if d < float(skaly[k][1]):
						p = c + (p - c) / maxf(d, 0.01) * float(skaly[k][1])
		hl[i] = p
	pes_osa = hl
	_pes_od_sten()
	# pole vzdalenosti (0,5 m) v pasu PES_DMAX kolem osy
	var w := int(stan_rect.size.x / PES_K)
	var h := int(stan_rect.size.y / PES_K)
	var px := PackedByteArray()
	px.resize(w * h)
	px.fill(255)
	var o := stan_rect.position
	for i in pes_osa.size() - 1:
		var a := pes_osa[i]
		var b := pes_osa[i + 1]
		if a == Vector2.INF or b == Vector2.INF:
			continue
		var lo := (a.min(b) - Vector2(PES_DMAX, PES_DMAX) - o) / PES_K
		var hi := (a.max(b) + Vector2(PES_DMAX, PES_DMAX) - o) / PES_K
		var ab := b - a
		for jj in range(maxi(0, int(lo.y)), mini(h, int(hi.y) + 1)):
			for ii in range(maxi(0, int(lo.x)), mini(w, int(hi.x) + 1)):
				var q := o + Vector2(ii, jj) * PES_K
				var t := clampf((q - a).dot(ab) / maxf(ab.length_squared(), 1e-6), 0.0, 1.0)
				var d := q.distance_to(a + ab * t)
				var v := clampi(int(d / PES_DMAX * 255.0), 0, 255)
				if v < px[jj * w + ii]:
					px[jj * w + ii] = v
	pes_dist = Image.create_from_data(w, h, false, Image.FORMAT_R8, px)
	print("pesiny: %d bodu osy, %d skal obejito" % [pes_osa.size(), skaly.size()])


## Vzdalenost od osy pesiny (m), bilinearne z pes_dist; za PES_DMAX vraci PES_DMAX. Cte se i z vlaken louky.
func pes_d(x: float, z: float) -> float:
	if pes_dist == null:
		return PES_DMAX
	var fx := (x - stan_rect.position.x) / PES_K
	var fz := (z - stan_rect.position.y) / PES_K
	var i := floori(fx)
	var j := floori(fz)
	if i < 0 or j < 0 or i >= pes_dist.get_width() - 1 or j >= pes_dist.get_height() - 1:
		return PES_DMAX
	fx -= i
	fz -= j
	var a := lerpf(pes_dist.get_pixel(i, j).r, pes_dist.get_pixel(i + 1, j).r, fx)
	var b := lerpf(pes_dist.get_pixel(i, j + 1).r, pes_dist.get_pixel(i + 1, j + 1).r, fx)
	return lerpf(a, b, fz) * PES_DMAX


## Useky pesin (a.x, a.z, b.x, b.z) za sebou pres vsechny pesiny (vstup pro _pes_postav).
func pes_useky() -> PackedVector4Array:
	var out := PackedVector4Array()
	for cesta: Array in PESINY:
		for q in range(cesta.size() - 1):
			out.append(Vector4(cesta[q].x, cesta[q].y, cesta[q + 1].x, cesta[q + 1].y))
	return out


## Vlnka osy pesiny (m kolmo k useku) ve vzdalenosti x od zacatku useku delky dl; konce useku drzi (navaznost).
static func _pes_o(x: float, dl: float, s: int) -> float:
	return 8.0 * sin(PI * x / dl) * (0.65 * sin(0.045 * x + 1.7 * s) + 0.35 * sin(0.11 * x + 4.1 * s))


## Prumer ctverce (2r+1)^2 bunek mrizky, po radcich a sloupcich.
static func _rozmaz_mriz(d: PackedFloat32Array, nx: int, nz: int, r: int) -> PackedFloat32Array:
	var a := PackedFloat32Array()
	a.resize(nx * nz)
	for j in nz:
		var s := 0.0
		for q in range(0, mini(r, nx - 1) + 1):
			s += d[j * nx + q]
		for i in nx:
			if i + r < nx and i > 0:
				s += d[j * nx + i + r]
			if i - r - 1 >= 0:
				s -= d[j * nx + i - r - 1]
			a[j * nx + i] = s / float(mini(i + r, nx - 1) - maxi(i - r, 0) + 1)
	var b := PackedFloat32Array()
	b.resize(nx * nz)
	for i in nx:
		var s := 0.0
		for q in range(0, mini(r, nz - 1) + 1):
			s += a[q * nx + i]
		for j in nz:
			if j + r < nz and j > 0:
				s += a[(j + r) * nx + i]
			if j - r - 1 >= 0:
				s -= a[(j - r - 1) * nx + i]
			b[j * nx + i] = s / float(mini(j + r, nz - 1) - maxi(j - r, 0) + 1)
	return b


func _stanoviste() -> void:
	var t0 := Time.get_ticks_msec()
	var g: Dictionary = data["trava_kraj"]
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var k := float(g["k"])
	var nx := int(g["nx"])
	var nz := int(g["nz"])
	stan_rect = Rect2(x0, z0, nx * k, nz * k)
	var ch: Array[PackedFloat32Array] = []
	for i in 4:
		var a := PackedFloat32Array()
		a.resize(nx * nz)
		ch.append(a)
	# stromy: koruna ~ 6 m kolem kmene
	for key: String in data["rostliny"]:
		if key.contains("_daleko"):
			continue
		var kind := key.substr(0, key.rfind("_"))
		var c := -1
		for j: String in JEHLICNATE:
			if kind.begins_with(j):
				c = 0
		if c < 0:
			for l: String in LISTNACE:
				if kind.begins_with(l):
					c = 1
		var skala := kind.begins_with("skala_")
		if c < 0 and not skala:
			continue
		# stromy: kryti korunou (radce 11:00 - stin dela koruna 8-12 m, ne kmen); polomer koruny z koule impostoru
		# (vodorovna pulka: sqrt(polomer^2 - (vyska/2)^2), nejmene 18 % vysky) x meritko instance
		var koruna := 3.0
		var imd := _imp_druh(kind) if c >= 0 else ""
		if imd != "":
			var im: Dictionary = _imp_meta[imd]
			koruna = maxf(sqrt(maxf(0.0, pow(float(im["polomer"]), 2.0) - pow(float(im["vyska"]) * 0.5, 2.0))), float(im["vyska"]) * 0.18)
		for t: Array in data["rostliny"][key]:
			var i0 := roundi((float(t[3]) - x0) / k)
			var j0 := roundi((float(t[11]) - z0) / k)
			var sc := Vector3(t[0], t[4], t[8]).length()
			var rm := (sc * 6.0 + 12.0) if skala else koruna * sc
			var rr := ceili(rm / k)
			for dj in range(-rr, rr + 1):
				for di in range(-rr, rr + 1):
					var i := i0 + di
					var j := j0 + dj
					if i < 0 or j < 0 or i >= nx or j >= nz:
						continue
					var dd := sqrt(float(di * di + dj * dj)) * k / maxf(rm, 0.5)
					var w := (1.0 - dd) if skala else (1.0 - smoothstep(0.7, 1.05, dd))
					if w <= 0.0:
						continue
					var a: PackedFloat32Array = ch[2 if skala else c]
					a[j * nx + i] = minf(1.0, a[j * nx + i] + w)
	# les je zapoj, ne jeden strom (radce 20:05 bod 5): kryti korunou plati jen tam, kde je v okoli 10 m prumerne
	# kryti >= 0,35 - samotny strom v louce nema pod sebou opad ani holou zem, louka pod nim zustava
	for c2 in 2:
		var hl := _rozmaz_mriz(_rozmaz_mriz(ch[c2], nx, nz, 2), nx, nz, 2)
		var hl2 := _rozmaz_mriz(_rozmaz_mriz(ch[1 - c2], nx, nz, 2), nx, nz, 2)
		for i in nx * nz:
			ch[c2][i] *= smoothstep(0.25, 0.45, hl[i] + hl2[i])
	# pesiny: osa obchazi skaly (_pes_postav). Kanal A = znamenkova vzdalenost od osy 0,5 + sd / 6 m (+-3 m): linearni
	# pole se bilinearne interpoluje presne i na mrizce 2 m. Samostatna textura pes_dist byla 14. vzorkovac zem.gdshader -
	# na Adrenu (16 jednotek, Godot si cast bere) se shader nesestavil a teren byl pruhledny (Misa 0.56).
	_pes_postav()
	var sd := PackedFloat32Array()
	sd.resize(nx * nz)
	sd.fill(3.0)
	var osa := pes_osa
	for si in osa.size() - 1:
		var a := osa[si]
		var b := osa[si + 1]
		if a == Vector2.INF or b == Vector2.INF:
			continue
		var zac := si == 0 or osa[si - 1] == Vector2.INF
		var kon := si + 2 >= osa.size() or osa[si + 2] == Vector2.INF
		var ab := b - a
		var l2 := maxf(ab.length_squared(), 1e-6)
		var i0 := maxi(0, int((minf(a.x, b.x) - 3.0 - x0) / k))
		var i1 := mini(nx - 1, int((maxf(a.x, b.x) + 3.0 - x0) / k) + 1)
		var j0 := maxi(0, int((minf(a.y, b.y) - 3.0 - z0) / k))
		var j1 := mini(nz - 1, int((maxf(a.y, b.y) + 3.0 - z0) / k) + 1)
		for j in range(j0, j1 + 1):
			for i in range(i0, i1 + 1):
				var q := Vector2(x0 + i * k, z0 + j * k)
				var t := (q - a).dot(ab) / l2
				var d := q.distance_to(a + ab * clampf(t, 0.0, 1.0))
				if d >= absf(sd[j * nx + i]):
					continue
				# za koncem pesiny kladne (jinak by zmena znamenka tahla pesinu dal po prodlouzene ose)
				var zn := 1.0 if (zac and t < 0.0) or (kon and t > 1.0) else signf(ab.cross(q - a))
				sd[j * nx + i] = d * (zn if zn != 0.0 else 1.0)
	# ch[3] (CPU, _st(3)) zustava maska "pesina do 3 m"; znamenkova hodnota jen do obrazku pro shader
	for i in nx * nz:
		ch[3][i] = clampf(1.0 - absf(sd[i]) / 3.0, 0.0, 1.0)
	var by := PackedByteArray()
	by.resize(nx * nz * 4)
	for i in nx * nz:
		for c in 3:
			by[i * 4 + c] = int(clampf(ch[c][i], 0.0, 1.0) * 255.0)
		by[i * 4 + 3] = roundi((0.5 + 0.5 * clampf(sd[i] / 3.0, -1.0, 1.0)) * 255.0)
	stanoviste = Image.create_from_data(nx, nz, false, Image.FORMAT_RGBA8, by)
	_st_ch = ch
	_st_n = Vector2i(nx, nz)
	var t1 := Time.get_ticks_msec()
	_krajina()
	print("stanoviste %d ms, krajina %d ms" % [t1 - t0, Time.get_ticks_msec() - t1])
	if _mats.has("zem"):
		_pudy(_mats["zem"] as ShaderMaterial)


## Kryti shora z offline casti (TVRZ_ROZSEV=1 -> modely/louka/kryti.bin, paprsky pod stoly, lavice, strechy,
## pavlac, skaly): bunka 32 m, mrizka 64 x 64 po 0,5 m.
const KRYTI_SOUBOR := "res://modely/louka/kryti.bin"
var kryti_tab := {}


func _nacti_kryti() -> void:
	if not kryti_tab.is_empty() or not FileAccess.file_exists(KRYTI_SOUBOR):
		return
	var by := FileAccess.get_file_as_bytes(KRYTI_SOUBOR)
	var o := 0
	while o + 516 <= by.size():
		var c := Vector2i(by.decode_s16(o), by.decode_s16(o + 2))
		var kr := PackedByteArray()
		kr.resize(4096)
		for i in 4096:
			kr[i] = (by[o + 4 + (i >> 3)] >> (i & 7)) & 1
		kryti_tab[c] = kr
		o += 516


## Cesta z tvrze (sit Teren_cesta, Misa 0.60: "cesta z hradu plna travy"): louka i rozsevy ji braly jako teren
## (jmeno Teren*). Trojuhelniky site do masky kryti (0,5 m) - na ceste nic neroste, okraj o 0,3 m dovnitr.
func _cesta_do_kryti() -> void:
	if _tvrz_root == null:
		return
	var mi := _tvrz_root.find_child("Teren_cesta", true, false) as MeshInstance3D
	if mi == null or mi.mesh == null:
		return
	var xf := mi.global_transform if mi.is_inside_tree() else mi.transform
	var n := 0
	for si in mi.mesh.get_surface_count():
		var a := mi.mesh.surface_get_arrays(si)
		var v: PackedVector3Array = a[Mesh.ARRAY_VERTEX]
		var idx: PackedInt32Array = a[Mesh.ARRAY_INDEX]
		for t in idx.size() / 3:
			var p0 := xf * v[idx[t * 3]]
			var p1 := xf * v[idx[t * 3 + 1]]
			var p2 := xf * v[idx[t * 3 + 2]]
			var tri := PackedVector2Array([Vector2(p0.x, p0.z), Vector2(p1.x, p1.z), Vector2(p2.x, p2.z)])
			var x0 := floorf(minf(minf(p0.x, p1.x), p2.x) * 2.0) / 2.0
			var z0 := floorf(minf(minf(p0.z, p1.z), p2.z) * 2.0) / 2.0
			var x1 := maxf(maxf(p0.x, p1.x), p2.x)
			var z1 := maxf(maxf(p0.z, p1.z), p2.z)
			var x := x0 + 0.25
			while x < x1:
				var z := z0 + 0.25
				while z < z1:
					if Geometry2D.is_point_in_polygon(Vector2(x, z), tri):
						var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
						if not kryti_tab.has(c):
							var kr := PackedByteArray()
							kr.resize(4096)
							kryti_tab[c] = kr
						var i := clampi(floori((x - c.x * 32.0) / 0.5), 0, 63)
						var j := clampi(floori((z - c.y * 32.0) / 0.5), 0, 63)
						(kryti_tab[c] as PackedByteArray)[j * 64 + i] = 2      # 2 = cesta (louka: ani nizky drn)
						n += 1
					z += 0.5
				x += 0.5
	print("cesta z tvrze v kryti: %d bodu" % n)


const VODNI := ["rakos", "orobinec", "vrba", "olse"]


var _sklony := PackedFloat32Array()     # sklon bunek mrizky trava_kraj (tan, nejvetsi z hran bunky) - skalni steny


## Sklon (tan) bunky vyskove mrizky v bode: terasy/skalni steny maji 1,2-18 (radce 06:40 bod 7). Mrizka 2 m, ctou ji
## smi_tu_byt (ve stene nic neroste) a _pata_sten.
func sklon_bunky(x: float, z: float) -> float:
	if _sklony.is_empty():
		_vyska(0.0, 0.0)
		if not _vys.has("trava_kraj"):
			return 0.0
		var g: Dictionary = _vys["trava_kraj"]
		var nx: int = g["nx"]
		var nz: int = g["nz"]
		var ys: PackedByteArray = g["y"]
		var kk := 100.0 * float(g["k"])
		_sklony.resize(nx * nz)
		for j in nz - 1:
			for i in nx - 1:
				var a := ys.decode_s16((j * nx + i) * 2)
				var b := ys.decode_s16((j * nx + i + 1) * 2)
				var c := ys.decode_s16(((j + 1) * nx + i) * 2)
				var d := ys.decode_s16(((j + 1) * nx + i + 1) * 2)
				_sklony[j * nx + i] = maxf(maxf(absi(b - a), absi(d - c)), maxf(absi(c - a), absi(d - b))) / kk
	var g2: Dictionary = _vys["trava_kraj"]
	var i2 := floori((x - float(g2["x0"])) / float(g2["k"]))
	var j2 := floori((z - float(g2["z0"])) / float(g2["k"]))
	if i2 < 0 or j2 < 0 or i2 >= int(g2["nx"]) - 1 or j2 >= int(g2["nz"]) - 1:
		return 0.0
	return _sklony[j2 * int(g2["nx"]) + i2]


## Skalni stena (radce 06:40 bod 7, FRONTA terasy): ve stene (sklon > 50 st.) nic neroste - trava, kere, stromy
## z exportu pryc; u paty sut (kameni, piskovcove bloky, cim vyssi stena, tim dal), na hrane obcas borovice.
func _pata_sten(pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	if sklon_bunky(0.0, 0.0) == 0.0 and _sklony.is_empty():
		return
	var pryc := 0
	for k: String in r.keys():
		if k.begins_with("skala_") or k.begins_with("balvan_"):
			continue
		# stromy uz od 42 st. (na svahu terasy by visely), ostatni nad 50 st.
		var strom := false
		for pf: String in LISTNACE + JEHLICNATE:
			if k.begins_with(pf):
				strom = true
		var mez := 0.9 if strom else 1.2
		var zust: Array = []
		for t: Array in r[k]:
			if sklon_bunky(float(t[3]), float(t[11])) < mez:
				zust.append(t)
		pryc += (r[k] as Array).size() - zust.size()
		r[k] = zust
	var g: Dictionary = _vys["trava_kraj"]
	var nx: int = g["nx"]
	var nz: int = g["nz"]
	var kr := float(g["k"])
	var gx0 := float(g["x0"])
	var gz0 := float(g["z0"])
	var ys: PackedByteArray = g["y"]
	# hrany: upravena terasa (_terasa_terenu, svah s pulbehem R2 na kazdou stranu) + zbyle kolme schody jinde
	var hrany: Array = []
	for e: Array in _terasa_hrany:
		hrany.append([e[0], e[1], e[2], e[3], true])
	for j in nz - 1:
		for i in nx - 1:
			for sm in 2:
				var a := ys.decode_s16((j * nx + i) * 2) / 100.0
				var b := ys.decode_s16(((j + sm) * nx + i + 1 - sm) * 2) / 100.0
				var dh := b - a
				if absf(dh) < 3.0 or absf(dh) / kr < 1.2:
					continue
				var dirv := Vector2(1 - sm, sm) * (-1.0 if dh > 0.0 else 1.0)
				hrany.append([Vector2(gx0 + i * kr, gz0 + j * kr) + Vector2(1 - sm, sm) * kr * 0.5, dirv, maxf(a, b), minf(a, b), false])
	var rng := RandomNumberGenerator.new()
	rng.seed = 6407
	var kameni := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_piskovec_1_0", "kamen_piskovec_2_0"]
	var ns := 0
	var nb := 0
	for e: Array in hrany:
		var mid: Vector2 = e[0]
		var dirv: Vector2 = e[1]
		var vys_st := float(e[2]) - float(e[3])
		var r2 := vys_st / (2.0 * tan(deg_to_rad(53.0))) if e[4] else kr * 0.5
		var pata := mid + dirv * r2
		var hrana := mid - dirv * r2
		if absf(pata.x + 4.0) < 90.0 and absf(pata.y) < 90.0 or Vector2(pata.x - 470.0, pata.y - 830.0).length() < 130.0:
			continue
		if e[4]:
			continue                                    # radce 18:00 bod 1: sut terasy vypnuta (levitovala nad travou)
		var dosah := 1.5 + vys_st * 0.22               # sut dobehne dal pod vyssi stenou
		for q in 2 + int(vys_st / 8.0):
			# sut od dolni tretiny svahu po dosah pod patou
			var p := pata + dirv * (dosah * pow(rng.randf(), 1.6) - r2 * 0.5 * rng.randf()) + dirv.orthogonal() * rng.randf_range(-1.0, 1.0) * kr
			if sklon_bunky(p.x, p.y) > 1.1 or pes_d(p.x, p.y) < 1.5 or _louka_m(p.x, p.y) < 0.03 and _les(p.x, p.y) < 0.1 and _st(2, p.x, p.y) < 0.1:
				continue
			var u := rng.randf()
			if u < 0.12:
				pridej.call("balvan_piskovec_2_0" if rng.randf() < 0.6 else "balvan_piskovec_1_0", p.x, p.y,
						rng.randf_range(0.5, 1.1), 0.3 * rng.randf_range(0.5, 1.1), 0.35)
				nb += 1
			elif u < 0.2 and e[4]:
				pridej.call("kapradi_%d_0" % (rng.randi() % 3 + 1), p.x, p.y, rng.randf_range(0.7, 1.2), 0.05)   # kapradi v suti
			else:
				pridej.call(kameni[rng.randi() % kameni.size()], p.x, p.y, clampf(exp(rng.randfn(0.4, 0.5)), 0.6, 3.5), -0.3, 0.4)
				ns += 1
		# borovice na hrane (Cesky raj): obcas, 2-4 m za hranou, kde je nahore rovina
		if vys_st > 6.0 and rng.randf() < 0.07 and r.has("borovice_0"):
			var p2 := hrana - dirv * rng.randf_range(2.0, 4.0) + dirv.orthogonal() * rng.randf_range(-1.0, 1.0)
			if sklon_bunky(p2.x, p2.y) < 0.6 and pes_d(p2.x, p2.y) > 2.0:
				var ref: Array = (r["borovice_0"] as Array)[0]
				var s0 := Vector3(ref[0], ref[4], ref[8]).length()
				(r["borovice_0"] as Array).append(_xf(p2.x, _vyska_min(p2.x, p2.y) - 0.15, p2.y, rng.randf() * TAU, s0 * rng.randf_range(0.7, 1.1),
						Vector3(rng.randf_range(-0.08, 0.08), 0, rng.randf_range(-0.08, 0.08))))
				pocty["borovice na hrane"] = int(pocty.get("borovice na hrane", 0)) + 1
	# _bloky_steny(pridej, pocty)      # radce 18:00 bod 1: bloky terasy skryt, az po vykonu znovu (osa podel hrany)
	pocty["ze steny pryc"] = pryc
	pocty["sut u paty"] = ns
	pocty["balvany u paty"] = nb


## Skalni stena terasy (radce 11:00 bod 2): do svahu zapustene velke balvany piskovce (fotosken), nepravidelne -
## ne rady vezi na boku (Misa 0.63: "hruza" - klady/jitrnice trcici ze svahu). Na kazde ~treti hrane terasy jeden
## balvan 3-6 m, 50 % pod terenem, nahodne natoceny a nakloneny; kolize trimesh (pridej).
func _bloky_steny(pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	if _terasa_hrany.is_empty() or not r.has("balvan_piskovec_1_0"):
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 1100
	var tg := tan(deg_to_rad(53.0))
	var mista: Array = []
	var n := 0
	for e: Array in _terasa_hrany:
		var D := float(e[2]) - float(e[3])
		if D < 5.0 or rng.randf() > 0.33:
			continue
		var mid: Vector2 = e[0]
		var dirv: Vector2 = e[1]
		var r2 := D / (2.0 * tg)
		# misto na svahu: od horni ctvrtiny po patu, bokem podel hrany
		var c := mid + dirv * rng.randf_range(-r2 * 0.6, r2 * 0.9) + dirv.orthogonal() * rng.randf_range(-1.0, 1.0)
		var volno := true
		for m: Vector2 in mista:
			if c.distance_to(m) < 9.0:
				volno = false
				break
		if not volno:
			continue
		mista.append(c)
		var k := "balvan_piskovec_%d_0" % (rng.randi() % 3 + 1)
		if not r.has(k):
			k = "balvan_piskovec_1_0"
		pridej.call(k, c.x, c.y, rng.randf_range(2.2, 3.8), -0.5, 0.45)
		n += 1
	pocty["skalni_stena_blok"] = n


## Jedno misto pro vsechny rozsevy (radce 11:20): smi tu rust bylina, kvet, ker, kamen, mrtve drevo?
## Ne pod strechou / stolem / lavici / pavlaci (kryti shora), ne v budove, ne na ceste, ve vode ani na dvore
## (maska louky 0 mimo les a skaly - dvur pred hostincem je 0), ne na pesine. Louka.gd cte tentyz zaklad.
func smi_tu_byt(x: float, z: float, druh := "") -> bool:
	var c := Vector2i(floori(x / 32.0), floori(z / 32.0))
	if kryti_tab.has(c):
		var i := clampi(floori((x - c.x * 32.0) / 0.5), 0, 63)
		var j := clampi(floori((z - c.y * 32.0) / 0.5), 0, 63)
		if (kryti_tab[c] as PackedByteArray)[j * 64 + i] != 0:
			return false
	for st: Array in _uvnitr:
		var q: Vector3 = (st[0] as Transform3D) * Vector3(x, 0.0, z)
		var b: AABB = st[1]
		if q.x > b.position.x and q.x < b.end.x and q.z > b.position.z and q.z < b.end.z:
			return false
	if sklon_bunky(x, z) > 1.2:
		return false                                  # skalni stena (radce 06:40 bod 7)
	if _st_ch.is_empty():
		return true
	# tvrz a ves maji vlastni teren mimo masku krajiny
	if absf(x + 4.0) < 75.0 and absf(z) < 70.0 or Vector2(x - 470.0, z - 830.0).length() < 130.0:
		return true
	for v: String in VODNI:
		if druh.begins_with(v):
			return true
	if koryto and (druh.begins_with("kamen") or druh.begins_with("balvan")) and not koryto.blizko(x, z).is_empty() \
			and float(koryto.blizko(x, z)[0]) < float(koryto.blizko(x, z)[2]) + 2.0:
		return true                                   # kameny v korytu a na brehu potoka
	if _st(3, x, z) > 0.5:
		return false                                  # pesina
	if _louka_m(x, z) < 0.03 and _les(x, z) < 0.1 and _st(2, x, z) < 0.1:
		return false                                  # cesta, voda, dvur, staveniste
	return true


## Kosena louka nebo pole (radce 17:00 a 20:05): maska louky z Blenderu, mimo les, skaly, pesiny, vodu, tvrz a ves, pod
## hrebeny (do 25 m). Tady nesmi byt vychozy, smrky ani kameni - jedna funkce pro rozsev i test (tools/test_svet.gd).
## Kosi se jen do 150 m od tvrze a vsi (radce 07:45: sec, pastva); dal louka_neudrzovana - zarostla.
const SEC_TVRZ := 225.0                # 75 m tvrz s nadvorim + 150 m
const SEC_VES := 280.0                 # 130 m ves + 150 m


## 0 = v dosahu kosy, 1 = 60 m a dal za nim (neudrzovana louka). Jen pocty: cte se i z vlaken louky.
static func divokost(x: float, z: float) -> float:
	var d := minf(Vector2(x + 4.0, z).length() - SEC_TVRZ, Vector2(x - 470.0, z - 830.0).length() - SEC_VES)
	# hranice seci zvlnena (+-4 m, radce 09:05: ne hrana), dve frekvence
	d += 3.0 * sin(x * 0.11 + z * 0.07) * cos(z * 0.13 - x * 0.05) + 1.5 * sin(x * 0.37 - z * 0.31)
	# val mezi hradbou a prikopem (Misa 0.63: "val u tvrze prazdny" - rovny posekany pruh): kosa tam nechodi,
	# neudrzovana trava (trsy, vysoka, byliny)
	if x > -31.5 and x < 22.5 and z > -20.5 and z < 21.5 and not (x > -27.6 and x < 18.5 and z > -16.6 and z < 17.4):
		return maxf(clampf(d / 60.0, 0.0, 1.0), 0.75)
	return clampf(d / 60.0, 0.0, 1.0)


func kosena_louka(x: float, z: float) -> bool:
	if absf(x + 4.0) < 75.0 and absf(z) < 70.0 or Vector2(x - 470.0, z - 830.0).length() < 130.0:
		return false
	if divokost(x, z) > 0.0:
		return false
	if _louka_m(x, z) <= 0.5 or _les(x, z) >= 0.1 or _st(2, x, z) >= 0.15 or _st(3, x, z) >= 0.3 or _vyska(x, z) >= 25.0:
		return false
	if koryto and not koryto.blizko(x, z).is_empty() and koryto.strop(x, z, false) < _vyska(x, z) + 1.0:
		return false                                   # zarez potoka
	if nadrz and not nadrz.misto(x, z).is_empty() and float(nadrz.misto(x, z)[0]) > -6.0:
		return false
	return true


## Hodnota kanalu stanoviste (0 jehlicnate, 1 listnate, 2 skaly, 3 pesina) v bode.
func _st(c: int, x: float, z: float) -> float:
	var i := clampi(roundi((x - stan_rect.position.x) / 2.0), 0, _st_n.x - 1)
	var j := clampi(roundi((z - stan_rect.position.y) / 2.0), 0, _st_n.y - 1)
	return _st_ch[c][j * _st_n.x + i]


func _les(x: float, z: float) -> float:
	return minf(1.0, _st(0, x, z) + _st(1, x, z))


var _maska_m := PackedByteArray()


## Mira louky z mrizky Blenderu (0 = cesta, voda, stavba, pole s nizsi vahou).
func _louka_m(x: float, z: float) -> float:
	var g: Dictionary = data["trava_kraj"]
	if _maska_m.is_empty():
		_maska_m = Marshalls.base64_to_raw(String(g["m"]))
	var i := clampi(roundi((x - float(g["x0"])) / float(g["k"])), 0, int(g["nx"]) - 1)
	var j := clampi(roundi((z - float(g["z0"])) / float(g["k"])), 0, int(g["nx"]) * 0 + int(g["nz"]) - 1)
	return _maska_m[j * int(g["nx"]) + i] / 255.0


## Krajina 07:50 (body 2-4): kameny vsude (pod skalami, v boru, na pesinach, na svazich, vychozy na hrbetech),
## kere v pasech (plast okraje lesa, pod skalami - ne uprostred kosene louky), les ve trech patrech (padle kmeny,
## parezy, kury, koreny, mech, nalet). Vse deterministicky z masky stanoviste; meritka podle prvni instance druhu.
func _krajina() -> void:
	var r: Dictionary = data["rostliny"]
	var mer := {}
	for k: String in r.keys():
		if not (r[k] as Array).is_empty():
			var t: Array = r[k][0]
			mer[k] = Vector3(t[0], t[4], t[8]).length()
	var tvary := {}
	var vysky := {}
	var pridej := func(k: String, x: float, z: float, s: float, ponor: float, naklon := 0.0, y := INF) -> void:
		if not r.has(k):
			r[k] = []
		var rr := RandomNumberGenerator.new()
		rr.seed = hash(Vector2(x, z))
		if ponor < 0.0:
			# zaporny ponor = podil vysky modelu (kameni zapustene o 30 %, radce 20:05 bod 7)
			if not vysky.has(k):
				var me0 := _skala_sit(k)
				vysky[k] = me0.get_aabb().size.y if me0 else 0.2
			ponor = -ponor * float(vysky[k]) * float(mer.get(k, 1.0)) * s
		var xf := _xf(x, (_vyska(x, z) if y == INF else y) - ponor, z, rr.randf() * TAU, float(mer.get(k, 1.0)) * s,
				Vector3(rr.randf_range(-naklon, naklon), 0, rr.randf_range(-naklon, naklon)))
		(r[k] as Array).append(xf)
		# balvany a padle kmeny: kolize (kolize sveta uz jsou postavene)
		if (k.begins_with("balvan_") or k.begins_with("dead_tree")) and _kolize_body:
			if not tvary.has(k):
				var me := _skala_sit(k)
				tvary[k] = [me.create_trimesh_shape(), me.get_aabb()] if me else null
			if tvary[k]:
				kolize(tvary[k][0], tvary[k][1], Transform3D(Basis(Vector3(xf[0], xf[4], xf[8]), Vector3(xf[1], xf[5], xf[9]), Vector3(xf[2], xf[6], xf[10])), Vector3(xf[3], xf[7], xf[11])))
	var rng := RandomNumberGenerator.new()
	rng.seed = 750
	var pocty := {}
	# vrba hlavata: kmen se rozsiruje jako vaza a pata visi nad zemi (hlaseni 0.54, 16:50) - zapustit 0,3 m
	for k: String in r.keys():
		if k.begins_with("vrba_hlavata"):
			for t: Array in r[k]:
				t[7] = float(t[7]) - 0.3
	# 1) kere uprostred louky pryc: jen v plasti lesa, u skal, u pesin a cest (m < 0,6) a kolem stavení
	for k: String in r.keys():
		if not (k.begins_with("shrub_02") or k.begins_with("sipek") or k.begins_with("bez_cerny")):
			continue
		var zust: Array = []
		for t: Array in r[k]:
			var x := float(t[3])
			var z := float(t[11])
			var okraj := maxf(maxf(_les(x + 12, z), _les(x - 12, z)), maxf(_les(x, z + 12), _les(x, z - 12)))
			if okraj > 0.15 or _les(x, z) > 0.1 or _st(2, x, z) > 0.1 or _louka_m(x, z) < 0.6 or _st(3, x, z) > 0.2:
				zust.append(t)
		pocty["kere pryc z louky"] = int(pocty.get("kere pryc z louky", 0)) + (r[k] as Array).size() - zust.size()
		r[k] = zust
	# 1b) kameni z exportu (14 700 kusu po cele krajine, stejne velke = "brouci", hlaseni 0.55): v kosene louce pryc,
	# zustava v boru, u pesin, pod skalami a u vody (kapitola 07:50)
	for k: String in r.keys():
		if not k.begins_with("kamen_"):
			continue
		var zust: Array = []
		for t: Array in r[k]:
			if not kosena_louka(float(t[3]), float(t[11])):
				zust.append(t)
		pocty["kameni pryc z louky"] = int(pocty.get("kameni pryc z louky", 0)) + (r[k] as Array).size() - zust.size()
		r[k] = zust
	var kere := ["shrub_02_0", "shrub_02_1", "sipek_0", "sipek_1", "bez_cerny_1_0", "bez_cerny_2_0", "bez_cerny_3_0"]
	var kameni := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_maly_4_0", "kamen_maly_5_0"]
	var x0 := stan_rect.position.x
	var z0 := stan_rect.position.y
	var krok := 4.0
	var z := z0 + 2.0
	while z < stan_rect.end.y - 2.0:
		var x := x0 + 2.0
		while x < stan_rect.end.x - 2.0:
			var px := x + rng.randf_range(-1.8, 1.8)
			var pz := z + rng.randf_range(-1.8, 1.8)
			x += krok
			if absf(px + 4.0) < 60.0 and absf(pz) < 55.0:
				continue                                    # tvrz a jeji bezprostredni okoli maji vlastni (_tvrz_zvenci)
			if Vector2(px - 470.0, pz - 830.0).length() < 110.0:
				continue                                    # ves ma vlastni dvory a zahrady
			var les := _les(px, pz)
			var jehl := _st(0, px, pz) / maxf(les, 0.01)
			var skal := _st(2, px, pz)
			var pes := _st(3, px, pz)
			var m := _louka_m(px, pz)
			var u := rng.randf()
			if u > 0.30:
				continue                                    # nic z nize nema vetsi pravdepodobnost nez 30 %
			var okraj := 0.0
			if les < 0.12 and m > 0.2:
				# plast lesa 15-20 m (hlaseni 0.54, 16:50: keř je na fotkach vzacnost): les do 9 a do 18 m od bodu
				for o: float in [9.0, 18.0]:
					okraj = maxf(okraj, maxf(maxf(_les(px + o, pz), _les(px - o, pz)), maxf(_les(px, pz + o), _les(px, pz - o))) * (1.0 if o < 10.0 else 0.8))
			var sklon := 0.0
			if les <= 0.25 and skal <= 0.45 and pes <= 0.55 and u < 0.09:
				sklon = Vector2(_vyska(px + 2, pz) - _vyska(px - 2, pz), _vyska(px, pz + 2) - _vyska(px, pz - 2)).length() / 4.0
			var k := ""
			var sc := 1.0
			var ponor := 0.05
			if les < 0.12 and okraj > 0.35 and m > 0.2 and u < 0.30:
				k = kere[rng.randi() % kere.size()]                    # plast okraje lesa
				sc = rng.randf_range(0.8, 1.4)
			elif skal > 0.45 and les < 0.9:
				if u < 0.45:
					k = kameni[rng.randi() % kameni.size()]          # sut pod skalami
					sc = clampf(exp(rng.randfn(0.5, 0.5)), 0.7, 4.0)
					ponor = 0.3
				elif u < 0.53:
					k = "balvan_piskovec_2_0" if rng.randf() < 0.6 else "balvan_piskovec_1_0"
					sc = rng.randf_range(0.5, 1.2)
					ponor = 0.3
				elif u < 0.60:
					k = kere[rng.randi() % 2]
			elif les > 0.25:
				if jehl > 0.5 and u < 0.10:
					k = kameni[rng.randi() % kameni.size()]          # kameni v boru
					sc = clampf(exp(rng.randfn(0.2, 0.5)), 0.5, 3.5)     # log-normalne: hodne malych, malo velkych
					ponor = 0.3
				elif jehl > 0.5 and u < 0.13:
					k = "kamen_piskovec_1_0"
					sc = rng.randf_range(0.6, 1.4)
					ponor = 0.15
				elif u < 0.155:
					k = "mech_%d_0" % (rng.randi() % 3 + 1)
					sc = rng.randf_range(0.04, 0.08)
				elif u < 0.165:
					k = "pine_sapling_small_0" if jehl > 0.5 else kere[rng.randi() % kere.size()]   # nalet
				elif u < 0.175 and jehl <= 0.5:
					k = "bark_debris_01_%d" % (rng.randi() % 4)
				elif u < 0.178:
					k = "dead_tree_trunk_0" if rng.randf() < 0.5 else "dead_tree_trunk_02_0"     # padle kmeny
					ponor = 0.15
				elif u < 0.182:
					k = ""                                           # vyvraceny koren jen u padleho kmene (nize)
				elif u < 0.192:
					k = "balvan_zula_1_0" if jehl <= 0.5 else "balvan_piskovec_3_0"           # zarostle balvany
					sc = rng.randf_range(0.4, 0.9)
					ponor = 0.35
			elif pes > 0.5 and pes < 0.75 and u < 0.06:
				k = kameni[rng.randi() % kameni.size()]              # kameni na kraji pesiny (0,8-1,5 m od osy)
				sc = clampf(exp(rng.randfn(0.0, 0.45)), 0.5, 2.5)
				ponor = 0.3
			elif sklon > 0.3 and m > 0.1 and u < 0.09:
				# svahy a strane (radce 17:00): nahore Cesky raj - piskovec, dole Posazavi - zula a droba (ohlazene, sede)
				var nahore := _vyska(px, pz) > 20.0
				var w2 := rng.randf()
				# jen balvany, drobne kameni na louce ne (radce 20:05 bod 7)
				if w2 < 0.5:
					k = ("balvan_piskovec_2_0" if rng.randf() < 0.6 else "balvan_piskovec_1_0") if nahore else ("balvan_zula_1_0" if rng.randf() < 0.5 else "balvan_droba_1_0")
					sc = clampf(exp(rng.randfn(0.0, 0.35)), 0.5, 1.6)
					ponor = 0.35
			if k != "":
				pridej.call(k, px, pz, sc, ponor * sc if not k.begins_with("kamen") else -0.3, 0.25)
				pocty[k.substr(0, k.rfind("_"))] = int(pocty.get(k.substr(0, k.rfind("_")), 0)) + 1
				# vyvraceny koren (hlaseni 0.54 bod 3): jen v lese vedle padleho kmene, ne sam na louce
				if k.begins_with("dead_tree") and les > 0.6:
					var rk := RandomNumberGenerator.new()
					rk.seed = hash(Vector2(pz, px))
					var ko := Vector2.from_angle(rk.randf() * TAU) * rk.randf_range(1.5, 3.0)
					if _les(px + ko.x, pz + ko.y) > 0.6 and _st(3, px + ko.x, pz + ko.y) < 0.4:
						pridej.call("root_cluster_01_0", px + ko.x, pz + ko.y, 1.0, 0.1, 0.25)
						pocty["root_cluster_01"] = int(pocty.get("root_cluster_01", 0)) + 1
		z += krok
	_vychozy(rng, pridej, pocty)
	_pata_sten(pridej, pocty)
	# kameny v korytu a na brehu potoka (radce 04:55 bod 4) a zarez udoli jako v Posazavi (hlaseni 0.54 bod 1, 16:50,
	# Misa: skalnaty kanon): balvany (zula, droba) v korytu a u paty brehu, na narazovem brehu zatacky skalni vychozy
	# a sut zapustene do svahu, na svahu a hrane keře (liska, bez, sipek) a olse/vrby; jesep na vnitrnim brehu oblazky
	if koryto:
		var kr = koryto
		var kam := ["kamen_maly_1_0", "kamen_maly_2_0", "kamen_maly_3_0", "kamen_maly_4_0", "kamen_maly_5_0", "kamen_zula_1_0", "kamen_zula_2_0"]
		var balv := ["balvan_zula_1_0", "balvan_droba_1_0"]
		var kere_v := ["shrub_02_0", "shrub_02_1", "bez_cerny_1_0", "bez_cerny_2_0", "sipek_0"]
		var nk := 0
		var nv := 0
		var nkr := 0
		var vys := func(x: float, z: float) -> float: return _vyska(x, z)
		for k in kr.body.size() - 1:
			var a: Vector2 = kr.body[k]
			var b: Vector2 = kr.body[k + 1]
			var nrm := (b - a).normalized().orthogonal()
			var w: float = kr.sirky[k]
			var dl := a.distance_to(b)
			var t := 0.0
			while t < dl:
				t += rng.randf_range(0.8, 2.2)
				var u := rng.randf()
				var o := a.lerp(b, minf(t, dl) / dl)
				var sg := 1.0 if rng.randf() < 0.5 else -1.0
				if u < 0.6:
					# na brehu a u kraje vody (pas w-0,4 .. w+1,4 na obou stranach)
					var of := rng.randf_range(w - 0.4, w + 1.4)
					var q := o + nrm * (of * sg)
					var sk := rng.randf_range(1.5, 4.0)
					pridej.call(kam[rng.randi() % kam.size()], q.x, q.y, sk, 0.05, 0.4)
				elif u < 0.8:
					# balvany v korytu, vycnivaji nad hladinu (obtekani, pena z peceni vody)
					var q := o + nrm * rng.randf_range(-w * 0.8, w * 0.8)
					var sb := rng.randf_range(0.5, 1.0)
					pridej.call(balv[rng.randi() % 2], q.x, q.y, sb, 0.25, 0.3)
					kameny_toku.append(Vector4(q.x, q.y, 0.55 * sb, atan2((b - a).y, (b - a).x)))
				nk += 1
			# zarez: kazdych ~3 m na kazde strane podle sirky zarezu (kde svah potka teren)
			t = 0.0
			while t < dl:
				t += rng.randf_range(2.0, 4.0)
				var o := a.lerp(b, minf(t, dl) / dl)
				for sg: float in [1.0, -1.0]:
					var smer: Vector2 = nrm * sg
					var hr: float = kr.hrana(o, smer, w, vys)
					var bl: Array = kr.blizko(o.x + smer.x * (w + 1.0), o.y + smer.y * (w + 1.0))
					var vn: float = float(bl[3]) if not bl.is_empty() else 0.0
					var svah := hr - w - 0.6                 # delka svahu (m)
					var u := rng.randf()
					if svah > 1.5 and vn < -0.3 and u < 0.55 * -vn:
						# narazovy breh: skalni vychoz (velky balvan zapusteny do svahu) a sut pod nim
						var dq := rng.randf_range(w + 1.0, maxf(w + 1.5, hr - 1.0))
						var q := o + smer * dq
						var sc := rng.randf_range(1.0, 2.2) * clampf(svah / 5.0, 0.6, 1.6)
						pridej.call(balv[rng.randi() % 2], q.x, q.y, sc, 0.5 * sc, 0.5)
						for m in 3:
							var q2 := o + smer * rng.randf_range(w + 0.6, dq) + (b - a).normalized() * rng.randf_range(-2.0, 2.0)
							pridej.call(kam[rng.randi() % kam.size()], q2.x, q2.y, rng.randf_range(2.0, 5.0), 0.08, 0.5)
						nv += 1
					elif svah > 1.0 and u < 0.25:
						# balvan zapusteny do svahu (ne prilepeny): pulka v zemi
						var q := o + smer * rng.randf_range(w + 1.2, hr)
						var sc := rng.randf_range(0.5, 1.3)
						pridej.call(balv[rng.randi() % 2], q.x, q.y, sc, 0.45 * sc, 0.4)
						nk += 1
					u = rng.randf()
					if u < 0.45:
						# kere na svahu a na hrane (az 3 m za ni); na jesepu ne
						var q := o + smer * rng.randf_range(w + 1.5 + 4.0 * maxf(vn, 0.0), hr + 3.0)
						if smi_tu_byt(q.x, q.y, "kere"):
							pridej.call(kere_v[rng.randi() % kere_v.size()], q.x, q.y, rng.randf_range(0.8, 1.4), 0.05)
							nkr += 1
		pocty["kameny v potoce"] = nk
		pocty["vychozy v zarezu"] = nv
		pocty["kere v zarezu"] = nkr
		pocty["kameny ve vode (cereni)"] = kameny_toku.size()
		_stromy_u_potoka(r, rng)
	# rakos a orobinec v pasu bahna u rybniku a prikopu (radce 04:55 bod 5)
	if nadrz:
		var vod := []
		for kk: String in ["rakos_1_0", "rakos_2_0", "orobinec_1_0", "orobinec_2_0"]:
			if r.has(kk) and not (r[kk] as Array).is_empty():
				vod.append(kk)
		var nr := 0
		for nd2: Dictionary in nadrz.nadrze:
			var dd: PackedFloat32Array = nd2["d"]
			for j in range(0, int(nd2["nz"]), 2):
				for i in range(0, int(nd2["nx"]), 2):
					var d: float = dd[j * int(nd2["nx"]) + i]
					if d > 0.25 or d < -1.2 or rng.randf() > 0.45 or vod.is_empty():       # jen pas bahna, ne ve vode
						continue
					var rx := float(nd2["x0"]) + i * 0.5 + rng.randf_range(-0.4, 0.4)
					var rz := float(nd2["z0"]) + j * 0.5 + rng.randf_range(-0.4, 0.4)
					var kk: String = vod[rng.randi() % vod.size()]
					var t := _xf(rx, minf(_vyska(rx, rz), float(nd2["y"])) - 0.05, rz, rng.randf() * TAU, float(mer.get(kk, 1.0)) * rng.randf_range(0.8, 1.25))
					(r[kk] as Array).append(t)
					nr += 1
		pocty["rakos u vody"] = nr
		pocty["prikop kameny"] = _prikop_kameny(r, rng, pridej)
	print("krajina 07:50: ", pocty)


## Vyska terenu u tvrze z vrcholu siti Teren* (po vyhloubeni prikopu): mrizka 1 m, nejvyssi vrchol v bunce,
## prazdne bunky z nejblizsiho souseda do 2 m. INF = nic.
func _vyska_sit(x: float, z: float) -> float:
	if _vys_sit.is_empty() and _tvrz_root:
		for mi in _tvrz_root.find_children("Teren*", "MeshInstance3D", true, false):
			var nm := String(mi.name)
			if nm == "Teren_obzor":
				continue
			var xf := (mi as MeshInstance3D).global_transform
			var me := (mi as MeshInstance3D).mesh
			for si in me.get_surface_count():
				for v: Vector3 in me.surface_get_arrays(si)[Mesh.ARRAY_VERTEX]:
					var w := xf * v
					if absf(w.x + 4.0) > 80.0 or absf(w.z) > 75.0:
						continue
					var c := Vector2i(floori(w.x), floori(w.z))
					_vys_sit[c] = maxf(float(_vys_sit.get(c, -INF)), w.y)
		_vys_sit[Vector2i(99999, 99999)] = 0.0             # postaveno (i kdyby bez vrcholu)
	var c0 := Vector2i(floori(x), floori(z))
	for rr in 3:
		var best := -INF
		for dx in range(-rr, rr + 1):
			for dz in range(-rr, rr + 1):
				best = maxf(best, float(_vys_sit.get(c0 + Vector2i(dx, dz), -INF)))
		if best > -INF:
			return best
	return INF


## Prikop tvrze (hlaseni 0.54, 16:50): hranu rozbit - u paty hradby (vnitrni breh) kamenna plenta z hustych kamenu
## v pasu 0-1,5 m od vody, na vnejsim svahu sut a balvany zapustene do svahu. Z pole vzdalenosti od brehu (nadrz.gd).
func _prikop_kameny(r: Dictionary, rng: RandomNumberGenerator, pridej: Callable) -> int:
	var stred := Vector2(-4.5, 0.4)
	var kam := ["kamen_zula_1_0", "kamen_zula_2_0", "kamen_piskovec_1_0", "kamen_maly_2_0", "kamen_maly_4_0"]
	var n := 0
	for nd: Dictionary in nadrz.nadrze:
		var nx := int(nd["nx"])
		var nz := int(nd["nz"])
		var x0 := float(nd["x0"])
		var z0 := float(nd["z0"])
		if Vector2(x0 + nx * 0.25, z0 + nz * 0.25).distance_to(stred) > 20.0:
			continue                                          # jen prikop kolem tvrze (rybnik je jinde)
		var dd: PackedFloat32Array = nd["d"]
		var y0 := float(nd["y"])
		# stredni vzdalenost vody od stredu tvrze: blize = vnitrni breh u hradby
		var vzd: Array = []
		for j in range(0, nz, 4):
			for i in range(0, nx, 4):
				if dd[j * nx + i] > 1.0:
					vzd.append(Vector2(x0 + i * 0.5, z0 + j * 0.5).distance_to(stred))
		if vzd.is_empty():
			continue
		vzd.sort()
		var stred_vody: float = vzd[vzd.size() / 2]
		for j in nz:
			for i in nx:
				var d := dd[j * nx + i]
				if d > 0.3 or d < -6.0 or rng.randf() > 0.5:
					continue
				var px := x0 + i * 0.5 + rng.randf_range(-0.25, 0.25)
				var pz := z0 + j * 0.5 + rng.randf_range(-0.25, 0.25)
				if absf(px + 3.0) < 4.0 and pz > 10.0:
					continue                                  # most a brana
				var vnitrni := Vector2(px, pz).distance_to(stred) < stred_vody
				var y := _vyska_sit(px, pz)
				if y == INF or y < y0 - 0.4:
					continue
				var k := ""
				var sc := 1.0
				var ponor := 0.05
				var u := rng.randf()
				if vnitrni and d > -1.5 and u < 0.3:
					k = kam[2 + rng.randi() % 3]              # plenta: husty pas kamenu u vody (levne site; zula jen na sut)
					sc = rng.randf_range(2.0, 3.2)
					ponor = 0.1
				elif not vnitrni and d > -6.0 and u < 0.06:
					k = kam[rng.randi() % kam.size()]         # sut na vnejsim svahu
					sc = rng.randf_range(1.0, 3.0)
				elif not vnitrni and d > -5.0 and u < 0.075:
					k = "balvan_zula_1_0" if rng.randf() < 0.5 else "balvan_droba_1_0"
					sc = rng.randf_range(0.5, 1.1)
					ponor = 0.45 * sc
				if k == "":
					continue
				pridej.call(k, px, pz, sc, ponor, 0.3, y)          # vyska ze site (val a prikop mrizka louky nezna)
				n += 1
	return n


## Stromy u potoka (hlaseni 0.54 bod 1): do 2 m od hrany zarezu a na jeho svahu jen olse a vrby (koreny pres breh),
## dub, lipa, buk, briza a smrk odtud pryc (i jejich vzdalene verze - stejny index instance); olse podel hrany.
func _stromy_u_potoka(r: Dictionary, rng: RandomNumberGenerator) -> void:
	var kr = koryto
	var vys := func(x: float, z: float) -> float: return _vyska(x, z)
	var blizko_hrany := func(x: float, z: float) -> bool:
		var bl: Array = kr.blizko(x, z)
		if bl.is_empty():
			return false
		return float(bl[0]) < float(bl[2]) + 0.6 or kr.strop(x, z) < _vyska(x, z) + 0.5 or float(kr.blizko(x, z)[0]) < _hrana_v(kr, x, z, vys) + 2.0
	var pryc := 0
	# Misa 0.60: "strom v rece a v moste zaroven" - zadny strom (ani olse a vrba) ve vode ani do 4 m od mostu
	var most := AABB()
	if _tvrz_root:
		var mm := _tvrz_root.find_child("Most_potok", true, false) as MeshInstance3D
		if mm:
			most = (mm.global_transform if mm.is_inside_tree() else mm.transform) * mm.get_aabb()
			most = most.grow(4.0)
	for key: String in r.keys():
		# u mostu nic vysokeho (Misa 0.62: "most ma zase v zabradli strom" - ker / mlady strom): stromy i kere
		var ker := key.begins_with("shrub") or key.begins_with("bez_") or key.begins_with("sipek") or key.begins_with("liska")
		if _strom_tvar(key.split("_daleko")[0]) == "" and not key.begins_with("vrba") and not key.begins_with("olse") and not ker:
			continue
		var par0 := key.replace("_0", "_daleko_0") if key.ends_with("_0") and not key.contains("_daleko") else ""
		var ma_par0 := par0 != "" and r.has(par0) and (r[par0] as Array).size() == (r[key] as Array).size()
		if key.contains("_daleko") and r.has(key.replace("_daleko", "")):
			continue                                  # vzdalena verze se filtruje s plnou (stejny index)
		var z1: Array = []
		var z2: Array = []
		for i in (r[key] as Array).size():
			var t: Array = r[key][i]
			var x := float(t[3])
			var z := float(t[11])
			var bl: Array = kr.blizko(x, z)
			var ve_vode := not bl.is_empty() and float(bl[0]) < float(bl[2]) + 0.3
			var u_mostu := most.size != Vector3.ZERO and x > most.position.x and x < most.end.x and z > most.position.z and z < most.end.z
			# Misa 0.60: male brizy v krajine rusi (svitici kura) - mladé (meritko < 0,3, pulka bříz) pryc
			var mala_briza := key.begins_with("briza") and Vector3(float(t[1]), float(t[5]), float(t[9])).length() < 0.3
			# tvrz, val a prikop: obrana - zadny strom u hradby ani v prikopu (Misa 0.61: bríza u zdi v prikopu)
			var u_tvrze := absf(x + 4.0) < 38.0 and absf(z) < 34.0
			if ker and not u_mostu:
				z1.append(t)
				if ma_par0:
					z2.append(r[par0][i])
				continue
			if ve_vode or u_mostu or mala_briza or u_tvrze:
				pryc += 1
				continue
			z1.append(t)
			if ma_par0:
				z2.append(r[par0][i])
		r[key] = z1
		if ma_par0:
			r[par0] = z2
	for key: String in r.keys():
		if key.contains("_daleko") or not (key.begins_with("dub") or key.begins_with("lipa") or key.begins_with("buk") \
				or key.begins_with("briza") or key.begins_with("smrk")):
			continue
		var par := key.replace("_0", "_daleko_0") if key.ends_with("_0") else ""
		var ma_par := par != "" and r.has(par) and (r[par] as Array).size() == (r[key] as Array).size()
		var zust: Array = []
		var zust2: Array = []
		for i in (r[key] as Array).size():
			var t: Array = r[key][i]
			if blizko_hrany.call(float(t[3]), float(t[11])):
				pryc += 1
				continue
			zust.append(t)
			if ma_par:
				zust2.append(r[par][i])
		r[key] = zust
		if ma_par:
			r[par] = zust2
	# olse podel hrany, kazdych 12-25 m strida strany (mlada a stredni, se vzdalenou verzi)
	var olse := 0
	var t0 := 0.0
	for k in kr.body.size() - 1:
		var a: Vector2 = kr.body[k]
		var b: Vector2 = kr.body[k + 1]
		t0 += a.distance_to(b)
		if t0 < rng.randf_range(12.0, 25.0):
			continue
		t0 = 0.0
		var nrm := (b - a).normalized().orthogonal() * (1.0 if rng.randf() < 0.5 else -1.0)
		var hr: float = kr.hrana(a, nrm, float(kr.sirky[k]), vys)
		var q := a + nrm * rng.randf_range(float(kr.sirky[k]) + 1.0, hr + 1.5)
		if not smi_tu_byt(q.x, q.y, "olse"):
			continue
		var druh := "olse_mlada" if rng.randf() < 0.4 else "olse_stredni"
		if not r.has(druh + "_0") or not r.has(druh + "_daleko_0") or (r[druh + "_0"] as Array).is_empty():
			continue
		var t1: Array = r[druh + "_0"][0]
		var mer := Vector3(t1[0], t1[4], t1[8]).length()
		var xf := _xf(q.x, _vyska(q.x, q.y) - 0.2, q.y, rng.randf() * TAU, mer * rng.randf_range(0.8, 1.2))
		(r[druh + "_0"] as Array).append(xf)
		(r[druh + "_daleko_0"] as Array).append(xf.duplicate())
		olse += 1
	print("stromy u potoka: pryc %d, olse %d" % [pryc, olse])


func _hrana_v(kr, x: float, z: float, vys: Callable) -> float:
	var bl: Array = kr.blizko(x, z)
	if bl.is_empty():
		return 0.0
	# smer od osy: kolmo podle gradientu vzdalenosti
	var e := 0.5
	var g := Vector2(float(kr.blizko(x + e, z)[0]) - float(kr.blizko(x - e, z)[0]) if not kr.blizko(x + e, z).is_empty() and not kr.blizko(x - e, z).is_empty() else 0.0,
			float(kr.blizko(x, z + e)[0]) - float(kr.blizko(x, z - e)[0]) if not kr.blizko(x, z + e).is_empty() and not kr.blizko(x, z - e).is_empty() else 0.0)
	if g.length() < 1e-4:
		return float(bl[2])
	g = g.normalized()
	var o := Vector2(x, z) - g * float(bl[0])
	return kr.hrana(o, g, float(bl[2]), vys)


## Skalni vychozy mimo skalni mesto (20-40 kusu): na hrbetech v lese, s borovici na vrcholu a kapradim u paty.
func _vychozy(rng: RandomNumberGenerator, pridej: Callable, pocty: Dictionary) -> void:
	var r: Dictionary = data["rostliny"]
	var key := "skala_hlava_0"
	if not r.has(key):
		return
	var sit := _skala_sit(key)
	var tvar := sit.create_trimesh_shape() if sit else null
	var bb := sit.get_aabb() if sit else AABB()
	var horni := _horni_plochy(sit) if sit else PackedVector3Array()
	var n := 0
	var pokus := 0
	while n < 30 and pokus < 4000:
		pokus += 1
		var x := rng.randf_range(stan_rect.position.x + 40, stan_rect.end.x - 40)
		var z := rng.randf_range(stan_rect.position.y + 40, stan_rect.end.y - 40)
		if _les(x, z) < 0.3 or _st(2, x, z) > 0.05 or absf(x + 4.0) < 90.0 and absf(z) < 90.0 or kosena_louka(x, z) or pes_d(x, z) < 8.0:
			continue
		var h := _vyska(x, z)
		var okoli := 0.0
		for q in 8:
			okoli += _vyska(x + cos(q * TAU / 8) * 25.0, z + sin(q * TAU / 8) * 25.0)
		if h - okoli / 8.0 < 3.0:
			continue                                         # jen hrbet nebo vrsek
		var s := rng.randf_range(4.0, 6.5) / maxf(bb.size.y, 1.0)
		var low := h
		for q in 8:
			low = minf(low, _vyska(x + cos(q * TAU / 8) * bb.size.x * s * 0.45, z + sin(q * TAU / 8) * bb.size.x * s * 0.45))
		var xf := _xf(x, low - 0.5 - bb.position.y * s, z, rng.randf() * TAU, s)
		(r[key] as Array).append(xf)
		for k2: String in ["skala_hlava_daleko_0", "skala_hlava_daleko2_0"]:
			if r.has(k2):
				(r[k2] as Array).append(xf)
		if tvar and _kolize_body:
			kolize(tvar, bb, Transform3D(Basis(Vector3(xf[0], xf[4], xf[8]), Vector3(xf[1], xf[5], xf[9]), Vector3(xf[2], xf[6], xf[10])), Vector3(xf[3], xf[7], xf[11])))
		# borovice na vrcholu (svisly paprsek na horni plochy vychozu), kapradi a sut u paty
		if r.has("borovice_0"):
			var xft := Transform3D(Basis(Vector3(xf[0], xf[4], xf[8]), Vector3(xf[1], xf[5], xf[9]), Vector3(xf[2], xf[6], xf[10])), Vector3(xf[3], xf[7], xf[11]))
			var inv := xft.affine_inverse()
			var o := inv * Vector3(x, low + 80.0, z)
			var dd := (inv.basis * Vector3.DOWN).normalized()
			var top := -INF
			for i in range(0, horni.size(), 3):
				var hh: Variant = Geometry3D.ray_intersects_triangle(o, dd, horni[i], horni[i + 1], horni[i + 2])
				if hh != null:
					top = maxf(top, (xft * (hh as Vector3)).y)
			if top == -INF:
				top = low - 0.5 + bb.size.y * s * 0.92
			var ref: Array = r["borovice_0"][0]
			(r["borovice_0"] as Array).append(_xf(x, top - 0.1, z, rng.randf() * TAU,
					Vector3(ref[0], ref[4], ref[8]).length() * rng.randf_range(0.5, 0.75)))
		for q in 6:
			var a := rng.randf() * TAU
			var d := bb.size.x * s * rng.randf_range(0.5, 0.8)
			pridej.call("kapradi_%d_0" % (q % 3 + 1) if q < 3 else "kamen_maly_%d_0" % (q % 5 + 1), x + cos(a) * d, z + sin(a) * d,
					rng.randf_range(0.8, 1.3) if q < 3 else rng.randf_range(1.0, 3.0), 0.05)
		n += 1
	pocty["vychozy"] = n


## Povrchy lesa a pesin (radce 07:50 bod 1) jako dve pole textur (jeden sampler: mobilni GPU maji 16 jednotek).
## 8 piskovec skalni steny (radce 06:40 bod 7): jen albedo, reliéf dela zem.gdshader z jasu (pudy_n ma 8 vrstev)
## Vrstva 0 se na PC (GL compat) kresli cerna -> mech (hrabanka) byl cerny a odrazel oblohu = modrobile "snehove"
## svahy (radce 0.63 skala, test pole vrstev); na 0 proto pesina, kterou zem.gdshader nepouziva, hrabanka je 4.
const PUDY := ["pesina", "les_listi", "les_jehlici", "les_pisek", "hrabanka", "oblazky", "blato", "kamen_lisejnik", "skala_piskovec"]


## Vrstva pole textur. t.get_image() cte texturu zpet z GPU a u ETC2 (na PC rozbalene pri nahrani) vracel nesmysl:
## data RGBA vydavana za ETC2 -> "rozbalena" do nahodnych barev (bily zrnity sum lisejniku, modrobile "snehove" svahy,
## bile skvrny v lese - Misa 0.61, radce 0.63 skala; zjisteno vypisem pixelu ve hre). Proto obrazek primo z importu
## (.ctex: hlavicka GST2 + surova data s mipmapami). Na PC bez ETC2 rozbalit na 512 px a mipmapy dopocitat
## (RGBA8 je 4x vetsi nez ETC2), tablet bere ETC2 primo.
func _pudy_img(t: Texture2D) -> Image:
	var im: Image = null
	var proc := ""
	if t is CompressedTexture2D:
		var cesta := (t as CompressedTexture2D).load_path
		var f := FileAccess.open(cesta, FileAccess.READ) if cesta != "" else null
		if f == null:
			proc = "nelze otevrit"
		elif f.get_length() < 52 or f.get_buffer(4).get_string_from_ascii() != "GST2":
			proc = "neni GST2"
		else:
			var ver := f.get_32()
			for q in 7:
				f.get_32()                      # sirka, vyska, priznaky, limit mipmap, 3 rezervy
			var df := f.get_32()
			var w := f.get_16()
			var h := f.get_16()
			var mm := f.get_32()
			var fmt := f.get_32()
			if ver != 1 or df != 0:
				proc = "verze %d / data %d" % [ver, df]
			elif w == 0 or h == 0 or fmt >= Image.FORMAT_MAX:
				proc = "hlavicka %dx%d format %d" % [w, h, fmt]
			else:
				var buf := f.get_buffer(f.get_length() - f.get_position())
				# velikost dat proti ocekavane (prazdny obrazek tehoz tvaru) - create_from_data by jinak hlasil chybu
				var vzor := Image.create_empty(w, h, mm > 0, fmt as Image.Format)
				if vzor == null or vzor.get_data_size() != buf.size():
					proc = "data %d B, cekano %d B" % [buf.size(), vzor.get_data_size() if vzor else -1]
				else:
					im = Image.create_from_data(w, h, mm > 0, fmt as Image.Format, buf)
		if im == null or im.is_empty():
			push_warning("pudy: %s - %s, beru get_image()" % [cesta, proc])
			im = null
	if im == null:
		im = t.get_image()
	if im == null or im.is_empty():
		push_warning("pudy: textura %s bez obrazku, sedy zastupce" % t.resource_path)
		im = Image.create_empty(512, 512, true, Image.FORMAT_RGBA8)
		im.fill(Color(0.3, 0.27, 0.22))
		im.generate_mipmaps()
	# PC bez ETC2: rozbalit (512 px, mipmapy dopocitat); tablet ETC2 beze zmeny (RAM)
	if im.is_compressed() and not RenderingServer.has_os_feature("etc2"):
		im = im.duplicate()
		im.decompress()
		im.clear_mipmaps()
		if im.get_width() > 512:
			im.resize(512, 512, Image.INTERPOLATE_BILINEAR)
		im.generate_mipmaps()
	return im


## Texture2DArray.create_from_images chce u vsech vrstev stejnou velikost, format i mipmapy (balik z_textury muze
## orezat jen nekterou .ctex). Kdyz nesedi: vsechny rozbalit a zmensit na nejmensi spolecnou velikost (vyjimka -
## pamet na chvili vic, varovani do logu); jinak beze zmeny.
func _pudy_sjednot(ims: Array[Image]) -> Array[Image]:
	var ok := true
	var w := 1 << 20
	for im: Image in ims:
		w = mini(w, mini(im.get_width(), im.get_height()))
		if im.get_size() != ims[0].get_size() or im.get_format() != ims[0].get_format() or im.has_mipmaps() != ims[0].has_mipmaps():
			ok = false
	if ok:
		return ims
	push_warning("pudy: vrstvy pole maji ruzny tvar - sjednocuji na %d px RGBA8" % w)
	var out: Array[Image] = []
	for im: Image in ims:
		var d := im.duplicate()
		if d.is_compressed():
			d.decompress()
		d.convert(Image.FORMAT_RGBA8)
		d.clear_mipmaps()
		d.resize(w, w, Image.INTERPOLATE_BILINEAR)
		d.generate_mipmaps()
		out.append(d)
	return out


func _pudy(s3: ShaderMaterial) -> void:
	var ia: Array[Image] = []
	var inn: Array[Image] = []
	var ks := PackedFloat32Array()
	for nm: String in PUDY:
		ia.append(_pudy_img(_t(nm, "diff")))
		if nm != "skala_piskovec":
			inn.append(_pudy_img(_t(nm, "nor")))
		# Misa 0.61: na svazich v lese bile/smetanove skvrny (pisek s jehlicim, svetle listi) - lesni puda tmavsi
		# 0.63: puvodni 0,65 tlumilo rozbity obrazek z get_image() (svetle skvrny); se spravnym .ctex v hlubokem stinu
		# lesa puda skoro cerna (snimek skala_t5_les1) -> 0,85
		var tm := 0.7 if nm.begins_with("les_") else (0.75 if nm == "oblazky" or nm == "blato" else 1.0)   # bile tecky na brehu prikopu
		if nm == "skala_piskovec":
			tm = 2.5                       # piskovec svetlejsi nez lesni puda (~0,2, sedobezovy jako bloky skal)
		ks.append(0.08 / maxf(float(_albedo().get(nm, 0.08)), 0.01) * tm)   # kalibrace odrazivosti (lesni puda ~0,08)
	var ta := Texture2DArray.new()
	ta.create_from_images(_pudy_sjednot(ia))
	var tn := Texture2DArray.new()
	tn.create_from_images(_pudy_sjednot(inn))
	s3.set_shader_parameter("pudy_a", ta)
	s3.set_shader_parameter("pudy_n", tn)
	s3.set_shader_parameter("pudy_k", ks)
	s3.set_shader_parameter("pudy_m", 2.2)
	s3.set_shader_parameter("stanoviste", ImageTexture.create_from_image(stanoviste))
	s3.set_shader_parameter("stan_k", float(data["trava_kraj"]["k"]))
	s3.set_shader_parameter("stan_rect", Vector4(stan_rect.position.x, stan_rect.position.y, stan_rect.size.x, stan_rect.size.y))


func _plants(parent: Node3D, quality: int) -> void:
	var root := Node3D.new()
	root.name = "Rostliny"
	# staticke MultiMeshe bez interpolace fyziky (project: physics_interpolation): s ni se zmena instance mimo krok
	# fyziky (dosednout) vratila zpet a kazda bunka nesla dvojity buffer
	root.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	parent.add_child(root)
	var keep_low: float = [0.3, 0.6, 1.0][quality]
	var keep_tree: float = [0.5, 0.8, 1.0][quality]
	var grass_mat := material("trava_divoka")
	var scenes := {}
	# pudorysy statickych staveb (hostinec, stan): uvnitr zadna trava, kapradi ani kere (rostla v krbu)
	var uvnitr: Array = []
	_nacti_kryti()
	_cesta_do_kryti()
	for n in parent.find_children("Staticky_*", "Node3D", true, false):
		var bb := AABB()
		var prvni := true
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var b := ((n as Node3D).global_transform.affine_inverse() * (mi as MeshInstance3D).global_transform) * (mi as MeshInstance3D).get_aabb()
			bb = b if prvni else bb.merge(b)
			prvni = false
		if not prvni and bb.size.x > 4.0 and bb.size.z > 4.0:
			uvnitr.append([(n as Node3D).global_transform.affine_inverse(), bb.grow(-0.1)])
	_uvnitr = uvnitr
	_smrky_na_listnace()
	_skalni_mesto()
	_lesni_patro()
	_tvrz_zvencí()
	_stanoviste()
	_les_hustsi()
	_lesni_puda()
	_kvetiny_louky()
	# _byliny_rozsev()                 # byliny z vetve assets: zastaveno (radce 18:00), zapnout po vykonu
	# vrba hlavata: model je useknuty valec bez korenu (hlaseni 0.55 bod 4) - skryta do noveho modelu z Blenderu
	for k: String in data["rostliny"].keys():
		if k.begins_with("vrba_hlavata"):
			data["rostliny"][k] = []
	# pravidla stanovist na konci pro vse, co rozsevy pridaly (radce 17:00, 20:05): v kosene louce ani smrk ani kameni
	var pryc := 0
	for k: String in data["rostliny"].keys():
		if not (k.begins_with("smrk_") or k.begins_with("kamen_")):
			continue
		var zust: Array = []
		for t: Array in data["rostliny"][k]:
			if not kosena_louka(float(t[3]), float(t[11])):
				zust.append(t)
		pryc += (data["rostliny"][k] as Array).size() - zust.size()
		data["rostliny"][k] = zust
	print("pravidla stanovist: smrku a kameni z kosene louky pryc ", pryc)
	# jeden pruchod na konci pro vse, co rozsevy pridaly (radce 20:05 bod 1: kameni koryta, prikopu, kere)
	if not _na_zem_arg.is_empty():
		_na_zem(_na_zem_arg[0], _na_zem_arg[1])
	_na_povrch(parent)
	_mekke_mimo_kvadry()
	_pesiny_volne()
	_most_bez_stromu()
	_stromy_mimo_balvany()
	_kmeny()
	# zakladni modely pred vzdalenymi verzemi: vzdalene LOD pak sdili materialy (a textury) zakladniho modelu
	var klice: Array = data["rostliny"].keys()
	klice.sort_custom(func(x: String, y: String) -> bool: return int(x.contains("_daleko")) < int(y.contains("_daleko")))
	var mat_zaklad := {}                 # druh -> {jmeno materialu: Material}
	var imp := {}                        # druh impostoru -> {bunka 256 m: [Color(pata xyz, meritko+otoceni)]}
	for key: String in klice:
		var kind := key.substr(0, key.rfind("_"))
		if not scenes.has(kind):
			var path := MOD + "rostliny/%s.glb" % kind
			if not ResourceLoader.exists(path):
				scenes[kind] = null
			else:
				scenes[kind] = (load(path) as PackedScene).instantiate()
		var inst: Node = scenes[kind]
		if inst == null:
			continue
		var mesh: Mesh = null
		for n in inst.find_children("*", "MeshInstance3D", true, false):
			if String(n.name) == key:
				mesh = (n as MeshInstance3D).mesh
		if mesh == null:
			continue
		if kind.contains("_daleko"):
			# LOD1/LOD2: stejne materialy jako plny model (jinak 3 kopie stejnych textur v graficke pameti)
			var zk: String = kind.left(kind.find("_daleko"))
			if mat_zaklad.has(zk):
				mesh = mesh.duplicate()
				for i in mesh.get_surface_count():
					var om := mesh.surface_get_material(i)
					var nm2 := om.resource_name if om else ""
					if (mat_zaklad[zk] as Dictionary).has(nm2):
						mesh.surface_set_material(i, mat_zaklad[zk][nm2])
		elif not mat_zaklad.has(kind):
			var md := {}
			for i in mesh.get_surface_count():
				var om := mesh.surface_get_material(i)
				if om:
					md[om.resource_name] = om
					# listi s pruhlednosti/predpruchodem (briza, smrk): ve stinu se kreslilo jako plny cerny tvar
					# (stinovy pruchod netestuje alfu) - alfa nuzky jako u dubu a lipy
					if om is BaseMaterial3D and (om as BaseMaterial3D).transparency in [BaseMaterial3D.TRANSPARENCY_ALPHA, BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS]:
						(om as BaseMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
						(om as BaseMaterial3D).alpha_scissor_threshold = 0.5
			# briza: kura svitila (Misa 0.60) - albedo kury o tretinu tmavsi, do sedobila
			if kind.begins_with("briza"):
				for nm_: String in md.keys():
					var km: Material = md[nm_]
					if km is BaseMaterial3D and (km as BaseMaterial3D).transparency == BaseMaterial3D.TRANSPARENCY_DISABLED:
						(km as BaseMaterial3D).albedo_color = (km as BaseMaterial3D).albedo_color * Color(0.62, 0.62, 0.6)
			# listi stromu: vlastni shader s vetrem a normalami od stredu koruny (0.61, Misa: placacky, zadny pohyb)
			if _strom_tvar(kind) != "" or kind.begins_with("bez_") or kind.begins_with("shrub") or kind.begins_with("vrba") \
					or kind.begins_with("ker_husty"):
				var bb := mesh.get_aabb()
				for nm_: String in md.keys():
					var lm: Material = md[nm_]
					if lm is BaseMaterial3D and (lm as BaseMaterial3D).transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR \
							and (lm as BaseMaterial3D).albedo_texture:
						md[nm_] = _listi_shader(lm as BaseMaterial3D, bb, _strom_tvar(kind) != "")
						# Misa 0.63 (tablet): duby a brizy moc zlute, smrky skoro cerne - odstin listi podle druhu
						# (prumerna barva listu z textur: dub 124/120/50 = zlutoolivova, smrk 59/67/57 = sedocerna)
						for pf: String in TINT_LISTI:
							if kind.begins_with(pf):
								var ti: Color = (md[nm_] as ShaderMaterial).get_shader_parameter("tint")
								(md[nm_] as ShaderMaterial).set_shader_parameter("tint", ti * (TINT_LISTI[pf] as Color).linear_to_srgb())   # tint je source_color (sRGB)
				for i in mesh.get_surface_count():
					var om3 := mesh.surface_get_material(i)
					if om3 and md.has(om3.resource_name) and md[om3.resource_name] is ShaderMaterial:
						mesh.surface_set_material(i, md[om3.resource_name])
			if kind.begins_with("skala_") and not kind.contains("_daleko2"):
				for nm_: String in md.keys():
					var om_: Material = md[nm_]
					if om_ is BaseMaterial3D and nm_.begins_with("skala") and (om_ as BaseMaterial3D).albedo_texture:
						md[nm_] = _skala_detail(om_ as BaseMaterial3D)
				for i in mesh.get_surface_count():
					var om2 := mesh.surface_get_material(i)
					if om2 and md.has(om2.resource_name):
						mesh.surface_set_material(i, md[om2.resource_name])
			mat_zaklad[kind] = md
		if kind == "divoka_trava":
			mesh = mesh.duplicate()
			for i in mesh.get_surface_count():
				var nm := mesh.surface_get_material(i).resource_name if mesh.surface_get_material(i) else ""
				mesh.surface_set_material(i, material(nm) if nm != "" else grass_mat)
		if kind == "divoka_trava" or kind == "grass_medium_01" or kind == "grass_medium_02":
			continue                      # travu dela louka (louka.gd); tyto trsy ji jen zdvojovaly (3,6 M troj. u tvrze)
		var low := NIZKE.has(kind) or PODROST.has(kind)
		var daleko := kind.ends_with("_daleko")
		if daleko and not kind.begins_with("skala_"):
			continue
		var tvar := _strom_tvar(kind)
		# K3: za plnym stromem impostor (pohled z atlasu); jednoduchy tvar jen kdyz impostor pro druh chybi
		var imp_druh := _imp_druh(kind) if tvar != "" else ""
		var tvar_mesh: Mesh = _tvar_mesh(tvar, mesh.get_aabb(), _listi(mesh)) if tvar != "" and imp_druh == "" else null
		var imp_s := mesh.get_aabb().size.y / float(_imp_meta[imp_druh]["vyska"]) if imp_druh != "" else 1.0
		var ma_lod: bool = data["rostliny"].has(kind + "_daleko_0")
		var mid := STREDNI.has(kind)
		var keep := keep_low if low else (keep_tree if not mid else 1.0)
		var cells := {}
		var k := 0
		for t: Array in data["rostliny"][key]:
			k += 1
			if keep < 1.0 and fmod(k * 0.6180339, 1.0) > keep:
				continue
			var xf := Transform3D(Basis(Vector3(t[0], t[4], t[8]), Vector3(t[1], t[5], t[9]), Vector3(t[2], t[6], t[10])),
					Vector3(t[3], t[7], t[11]))
			# mech u skal byl v exportu zvetseny 25-50x (vyska 0.6-1.6 m misto cm): plachty 30 m ve vzduchu
			if kind.begins_with("mech_") or kind.begins_with("moss_") or kind.begins_with("rock_moss"):
				var sc := xf.basis.get_scale().x
				if sc > 2.0:
					xf.basis = xf.basis.scaled(Vector3.ONE * (randf_range(0.8, 1.6) / sc))
			if (low or mid) and not smi_tu_byt(xf.origin.x, xf.origin.z, kind):
				continue
			var c := Vector2i(floori(xf.origin.x / BUNKA), floori(xf.origin.z / BUNKA))
			if not cells.has(c):
				cells[c] = []
			cells[c].append(xf)
		for c: Vector2i in cells:
			var list: Array = cells[c]
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = mesh
			mm.instance_count = list.size()
			for i in list.size():
				mm.set_instance_transform(i, list[i])
			var mmi := MultiMeshInstance3D.new()
			mmi.multimesh = mm
			mmi.name = "%s_%d_%d" % [key, c.x, c.y]
			if SBER.has(kind):
				for i in list.size():
					sber_spots.append({"id": SBER[kind], "mmi": mmi, "i": i, "xf": list[i]})
			# ROZPOCET (1500 kresleni, 2 M troj.): skaly LOD0 do 40 m (jen ta vrha stin), LOD1 40-120 m, LOD2 dal;
			# stromy plne do 60 m (stin), dal jednoduchy tvar bez stinu; ostatni vegetace stiny nevrha vubec
			var stin_ok := quality > 0
			var off := GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			var on := GeometryInstance3D.SHADOW_CASTING_SETTING_ON if stin_ok else off
			mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
			mmi.cast_shadow = off
			if imp_druh != "":
				mmi.visibility_range_end = STROM_PREP
				mmi.visibility_range_end_margin = 10.0
				mmi.cast_shadow = on
				for xf: Transform3D in list:
					var bc := Vector2i(floori(xf.origin.x / IMP_BUNKA), floori(xf.origin.z / IMP_BUNKA))
					if not imp.has(imp_druh):
						imp[imp_druh] = {}
					if not imp[imp_druh].has(bc):
						imp[imp_druh][bc] = []
					var yaw := fposmod(atan2(-xf.basis.x.z, xf.basis.x.x), TAU)
					var sc := xf.basis.get_scale().y * imp_s
					imp[imp_druh][bc].append(Color(xf.origin.x, xf.origin.y, xf.origin.z, roundf(sc * 256.0) + yaw / TAU * 0.999))
			elif tvar_mesh:
				mmi.visibility_range_end = STROM_PREP
				mmi.visibility_range_end_margin = 10.0
				mmi.cast_shadow = on
				var mm2 := MultiMesh.new()
				mm2.transform_format = MultiMesh.TRANSFORM_3D
				mm2.mesh = tvar_mesh
				mm2.instance_count = list.size()
				for i in list.size():
					mm2.set_instance_transform(i, list[i])
				var far := MultiMeshInstance3D.new()
				far.multimesh = mm2
				far.name = mmi.name + "_tvar"
				far.visibility_range_begin = STROM_PREP - 5.0
				far.visibility_range_begin_margin = 10.0
				far.visibility_range_end = STROM_DOHLED
				far.visibility_range_end_margin = 15.0
				far.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
				far.cast_shadow = off
				root.add_child(far)
			elif kind.begins_with("skala_"):
				if kind.ends_with("_daleko2"):
					mmi.visibility_range_begin = SKALA_LOD1
					mmi.visibility_range_end = 500.0
					mmi.visibility_range_end_margin = 40.0
				elif daleko:
					mmi.visibility_range_begin = SKALA_LOD0
					mmi.visibility_range_end = SKALA_LOD1
					mmi.visibility_range_end_margin = 10.0
				else:
					mmi.visibility_range_end = SKALA_LOD0
					mmi.visibility_range_end_margin = 5.0
					mmi.cast_shadow = on
			elif daleko:
				mmi.visibility_range_begin = LOD_M
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
			elif ma_lod:
				mmi.visibility_range_end = LOD_M
			elif low:
				mmi.visibility_range_end = [18.0, 25.0, 40.0][quality]       # louka (drn + trsy) pokryva dal
				mmi.visibility_range_end_margin = 6.0
			elif mid:
				mmi.visibility_range_end = [50.0, 70.0, 95.0][quality]
				mmi.visibility_range_end_margin = 10.0
				# radce 18:45 (0.64 FPS venku): lesni puda (kere, mlade jehlicnany, vetve, parezy) na tabletu jen do 40 m
				# - kostelik: puda 0,91 M; kameny, rakos a kmeny zustavaji (vyrazne v krajine)
				var puda := false
				for pf: String in ["shrub", "sipek", "bez_cerny", "ker_husty", "fir_sapling", "pine_sapling", "dry_branches", "tree_stump", "root_cluster", "rock_moss"]:
					if kind.begins_with(pf):
						puda = true
				if puda and (OS.has_feature("mobile") or OS.has_environment("TVRZ_MOBIL")):
					mmi.visibility_range_end = 40.0
					mmi.visibility_range_end_margin = 6.0
			elif kind.begins_with("balvan_") or kind.begins_with("kamen_"):
				# 0.60: balvany 1-2 m a kameny se kreslily do 450 m (prikop: 84 kresleni, 3 plochy na kus) - dal jsou pixel
				var bal := kind.begins_with("balvan_")
				mmi.visibility_range_end = ([100.0, 140.0, 200.0] if bal else [60.0, 90.0, 120.0])[quality]
				mmi.visibility_range_end_margin = 15.0
			else:
				mmi.visibility_range_end = [300.0, 450.0, 650.0][quality]
				mmi.visibility_range_end_margin = 40.0
			root.add_child(mmi)
	_impostory(root, imp)
	for kind: String in scenes:
		if scenes[kind]:
			(scenes[kind] as Node).free()


## Trava ve vsi: husté levne trsy (3 zkrizene karty) podle mrizky z Blenderu (vyska terenu, hustota).
## Na cestach, ve dvorech a v domech nic, u plotu a na loukach husteji.
func _ves_grass(parent: Node3D, quality: int) -> void:
	var g: Dictionary = data.get("trava_ves", {})
	if g.is_empty():
		return
	var n := int(g["n"])
	var k := float(g["k"])
	var x0 := float(g["x0"])
	var z0 := float(g["z0"])
	var ys := Marshalls.base64_to_raw(String(g["y"]))
	var ms := Marshalls.base64_to_raw(String(g["m"]))
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = load("res://obrazky/trava_karta.png")
	mat.albedo_color = Color(0.6, 0.64, 0.44)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.45
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.vertex_color_use_as_albedo = true
	mat.roughness = 0.85
	mat.backlight_enabled = true
	mat.backlight = Color(0.22, 0.27, 0.08)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for q in 3:
		var ang := PI * q / 3.0
		var tg := Vector3(cos(ang), 0, sin(ang)) * 0.4
		var up := Vector3(0, 0.6, 0)
		var pts := [-tg, tg, tg + up, -tg + up]
		var uvs := [Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)]
		var cols := [Color(0.55, 0.58, 0.5), Color(0.55, 0.58, 0.5), Color(1, 1, 1), Color(1, 1, 1)]
		for i: int in [0, 1, 2, 0, 2, 3]:
			st.set_color(cols[i])
			st.set_uv(uvs[i])
			st.set_normal(Vector3.UP)
			st.add_vertex(pts[i])
	var mesh := st.commit()
	mesh.surface_set_material(0, mat)
	grass_mesh = mesh
	return                                        # travu ve vsi dela louka.gd (mrizka trava_ves)
	var step: float = [0.95, 0.75, 0.62][quality]
	var rng := RandomNumberGenerator.new()
	rng.seed = 1393
	var cells := {}
	var lim := (n - 1) * k
	var x := 0.0
	while x < lim:
		var z := 0.0
		while z < lim:
			var px := x + rng.randf_range(-0.4, 0.4) * step
			var pz := z + rng.randf_range(-0.4, 0.4) * step
			z += step
			if px < 0.0 or pz < 0.0 or px >= lim or pz >= lim:
				continue
			var i := int(px / k)
			var j := int(pz / k)
			var fx := px / k - i
			var fz := pz / k - j
			var a0 := j * n + i
			var dens := lerpf(lerpf(ms[a0], ms[a0 + 1], fx), lerpf(ms[a0 + n], ms[a0 + n + 1], fx), fz) / 255.0
			if rng.randf() > dens * 1.1:
				continue
			var h0 := ys.decode_s16(a0 * 2)
			var h1 := ys.decode_s16((a0 + 1) * 2)
			var h2 := ys.decode_s16((a0 + n) * 2)
			var h3 := ys.decode_s16((a0 + n + 1) * 2)
			var hy := lerpf(lerpf(h0, h1, fx), lerpf(h2, h3, fx), fz) / 100.0
			var sc := rng.randf_range(0.55, 1.2) * lerpf(0.7, 1.1, dens)
			var xf := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc, sc * rng.randf_range(0.75, 1.35), sc)),
					Vector3(x0 + px, hy - 0.04, z0 + pz))
			var c := Vector2i(floori(xf.origin.x / BUNKA), floori(xf.origin.z / BUNKA))
			if not cells.has(c):
				cells[c] = []
			cells[c].append(xf)
		x += step
	var root := Node3D.new()
	root.name = "TravaVes"
	parent.add_child(root)
	var total := 0
	for c: Vector2i in cells:
		var list: Array = cells[c]
		var cen := Vector3((c.x + 0.5) * BUNKA, 0.0, (c.y + 0.5) * BUNKA)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = list.size()
		for i in list.size():
			var t: Transform3D = list[i]
			t.origin -= cen
			mm.set_instance_transform(i, t)
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.position = cen
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.visibility_range_end = [30.0, 42.0, 55.0][quality]
		mmi.visibility_range_end_margin = 8.0
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		root.add_child(mmi)
		total += list.size()
	print("trava ve vsi: ", total, " trsu")


## Pevne predmety z katalogu (bozi muka na krizovatce): model z modely/predmety, kolize kvadrem.
var _stavby: Array = []                # [stred xz, polomer] staticke stavby (zricenina, stan, hostinec) - pesiny je obchazeji


func _static_items(parent: Node3D) -> void:
	var katalog: Dictionary = {}
	var fk := FileAccess.open(MOD + "predmety.json", FileAccess.READ)
	if fk:
		katalog = JSON.parse_string(fk.get_as_text())
	for it: Dictionary in data.get("staticke", []):
		var id := String(it["id"])
		var ps: PackedScene = load(MOD + "predmety/" + id + ".glb")
		if ps == null:
			continue
		var n := Node3D.new()
		n.name = "Staticky_" + id
		var a: Array = it["p"]
		n.position = Vector3(a[0], a[1], a[2])
		n.rotation.y = float(it.get("yaw", 0.0))
		parent.add_child(n)
		n.add_child(ps.instantiate())
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var ab := (mi as MeshInstance3D).global_transform * (mi as MeshInstance3D).get_aabb()
			if ab.size.y > 0.5 and maxf(ab.size.x, ab.size.z) > 0.6:
				_stavby.append([Vector2(ab.get_center().x, ab.get_center().z), maxf(ab.size.x, ab.size.z) * 0.5 + 1.2])
		# modely od Misi (nove._import_sketchup): materialy pojmenovane podle hernich -> stejne fotky jako stavby
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			var msh := (mi as MeshInstance3D).mesh
			for i in msh.get_surface_count():
				var om := msh.surface_get_material(i)
				if om and data["materialy"].has(om.resource_name.split(".")[0]):
					(mi as MeshInstance3D).set_surface_override_material(i, material(om.resource_name))
		if it.has("boxy"):
			# stavba s jednoduchymi kolizemi (stan: stoly, sudy, platno; provazy a koliky bez kolize)
			var sb := StaticBody3D.new()
			for q: Array in it["boxy"]:
				var c := CollisionShape3D.new()
				var bx := BoxShape3D.new()
				bx.size = Vector3(q[3], q[4], q[5])
				c.shape = bx
				c.position = Vector3(q[0], q[1], q[2])
				sb.add_child(c)
			n.add_child(sb)
			continue
		if String(it.get("kolize", "")) == "trimesh":
			# stavba (hostinec, stan): presna kolize ze site, dovnitr se da vejit
			# model z importu (hostinec): kolize jen z puvodni site <id>_kolize, ta se nekresli
			var vse := n.find_children("*", "MeshInstance3D", true, false)
			var kol := vse.filter(func(m: Node) -> bool: return String(m.name).ends_with("_kolize"))
			for mi in vse:
				if kol.is_empty() or mi in kol:
					_trimesh(mi as MeshInstance3D)
				if mi in kol:
					(mi as MeshInstance3D).visible = false
				else:
					(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
			continue
		var r: Array = katalog.get(id, {}).get("rozmer", [1.0, 1.0, 1.0])
		var b := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var bs := BoxShape3D.new()
		bs.size = Vector3(float(r[0]) * 0.7, float(r[1]), float(r[2]) * 0.7)
		cs.shape = bs
		cs.position.y = float(r[1]) * 0.5
		b.add_child(cs)
		n.add_child(b)

