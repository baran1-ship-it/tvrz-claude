extends Node3D
## Zajímavá místa (Míša 15. 11., docs/zajimava_mista_plan.md): data hra/data/zajimava_mista.json z nastroje/zajimava_mista.py
## (poloha, natočení a výška každého dílu už spočtené – tablet jen načítá). Díly:
## - model les/…: lesní díly od modeláře (modely/les, kolize -convcolonly / -colonly z importu), LOD0 do lod0_do_m, _lod1 dál
## - zemljanka_*: chýše Havrana předělaná na zemljanku (modely/stavby_h, kolize OMI jako domy), podrobně do podrobny_do_m, dál _Daleko
## - stola: zkrácená štola (vstup z dálky, chodba zblízka), světla kahanů, víko kolize nad chodbou z viditelné sítě terénu
##   (kolize terénu je nad chodbou snížená – teren_dlazdice.py; víko je jednostranné, zevnitř chodby nepřekáží)
## - mlyn: mlýn Havrana bez dílového terénu, točí se kolo a čepový palečník (scripts/mlyn_kolo.gd jako Havran svet.gd _mlyn_dil)
## - predmet / balvan / strom: modely katalogu Havrana (předměty, kameny, stromy) s konvexní kolizí; strom s brtí (brt.glb)
## - efekt: milíř (kouř z průduchů, žár), smolárna (kouř, oheň), oheň (plamen jako louče)
const LES := "res://modely/les/"
const Pravidla := preload("res://scripts/pravidla.gd")
var d: Dictionary = {}
var hlavni: Node


func _ready() -> void:
	name = "Zajimava"
	hlavni = get_parent()
	if not FileAccess.file_exists("res://data/zajimava_mista.json"): return
	d = JSON.parse_string(FileAccess.get_file_as_string("res://data/zajimava_mista.json"))
	var n := 0
	for m: Dictionary in d["mista"]:
		var u := Node3D.new(); u.name = "Z_" + String(m["id"]); add_child(u)
		u.set_meta("nazev", m["nazev"]); u.set_meta("znacka", m["znacka"]); u.set_meta("stred", Vector3(float(m["x"]), float(m["y"]), float(m["z"])))
		for di: Dictionary in m["dily"]:
			var x := _dil(u, di, m)
			if x:
				n += 1
				if di.has("funkce"): x.set_meta("funkce", String(di["funkce"]))   # funkce.gd: sběr (uhlí, med, smola, kámen) u dílu
	_vika()
	print("ZAJIMAVA míst %d, dílů %d" % [get_child_count(), n])


func _xf(di: Dictionary) -> Transform3D:
	var s := float(di.get("meritko", 1.0))
	return Transform3D(Basis(Vector3.UP, float(di["yaw"])).scaled(Vector3(s, s, s)), Vector3(float(di["x"]), float(di["y"]), float(di["z"])))


func _dil(u: Node3D, di: Dictionary, m: Dictionary) -> Node3D:
	var lod: Dictionary = d["lod_les"]
	if di.has("model"):
		var mo := String(di["model"])
		if mo.begins_with("les/"):
			return _les(u, di, mo.substr(4))
		if mo.begins_with("zemljanka"):
			return _zemljanka(u, di, mo)
		if mo == "stola":
			return _stola(u, di)
		if mo == "mlyn":
			return _mlyn(u, di, m)
	if di.has("predmet"):
		var c := "res://modely/predmety_h/%s.glb" % di["predmet"]
		if not ResourceLoader.exists(c): push_warning("ZAJIMAVA předmět %s chybí" % c); return null
		var p := (load(c) as PackedScene).instantiate() as Node3D
		p.name = "P_" + String(di["predmet"]); p.transform = _xf(di); u.add_child(p)
		_dosah(p, float(lod["lod0_do_m"]))
		_kolize_konvexni(p)
		if String(di.get("efekt", "")) == "ohen": _ohen(u, p.global_position + Vector3.UP * 0.15)
		return p
	if di.has("balvan"):
		var c2 := LES + "%s.glb" % di["balvan"]
		if not ResourceLoader.exists(c2): return null
		var b := (load(c2) as PackedScene).instantiate() as Node3D
		b.name = "B_" + String(di["balvan"]); b.transform = _xf(di); u.add_child(b)
		_dosah(b, float(lod["lod1_do_m"]) if float(di.get("meritko", 1.0)) > 1.8 else float(lod["male_lod1_do_m"]))
		_kolize_konvexni(b)
		return b
	if di.has("strom"):
		return _strom(u, di)
	if di.has("scena"):   # hotová scéna Godotu (houně od modeláře – Luzka_1400, bez kolize)
		if not ResourceLoader.exists(String(di["scena"])): return null
		var sc := (load(String(di["scena"])) as PackedScene).instantiate() as Node3D
		sc.transform = _xf(di); u.add_child(sc)
		for g in sc.find_children("*", "GeometryInstance3D", true, false):
			if (g as GeometryInstance3D).visibility_range_begin > 0.0: (g as GeometryInstance3D).visibility_range_end = float(lod["lod0_do_m"])
		return sc
	return null


## lesní díl: LOD0 (kolize z importu) a _lod1 (bez kolize) přes Visibility Range
func _les(u: Node3D, di: Dictionary, jm: String) -> Node3D:
	var lod: Dictionary = d["lod_les"]
	var c0 := LES + jm + ".glb"; var c1 := LES + jm + "_lod1.glb"
	if not ResourceLoader.exists(c0): push_warning("ZAJIMAVA model %s chybí (nastroje/zajimava_modely.py)" % c0); return null
	var k := Node3D.new(); k.name = jm; k.transform = _xf(di); u.add_child(k)
	var l0 := (load(c0) as PackedScene).instantiate() as Node3D; l0.name = "LOD0"; k.add_child(l0)
	_barva_vrcholu(l0)   # NAVOD_LES.md: mech, saze, uhelný prach v barvě vrcholů (COLOR_0 převedené na sRGB – nastroje/barvy_vrcholu.py sada les)
	var d0 := float(lod["lod0_do_m"])
	var male := jm.begins_with("les_kriz") or jm.begins_with("les_bozi") or jm == "les_uhlir_naradi"
	var d1 := float(di.get("lod1_do_m", lod["male_lod1_do_m"] if male else lod["lod1_do_m"]))
	_dosah(l0, d0)
	if ResourceLoader.exists(c1):
		var l1 := (load(c1) as PackedScene).instantiate() as Node3D; l1.name = "LOD1"; k.add_child(l1)
		for g in l1.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).visibility_range_begin = d0; (g as GeometryInstance3D).visibility_range_end = d1
		for c in l1.find_children("*", "CollisionObject3D", true, false): c.queue_free()
	if String(di.get("funkce", "")) == "studanka": call_deferred("_voda_studanky", k)   # hlavni.mat_voda vzniká až po zajímavých místech
	match String(di.get("efekt", "")):
		"milir": _milir(k)
		"smolarna": _smolarna(k)
	return k


## Hladina studánky shaderem vody potoků (Míša 16. 11.; zajimava_mista.json funkce.studanka.voda): plocha materiálu modeláře
## M_LesVoda (šachta a potůček) zůstane tvarem, dostane UV shaderu (UV.x = metry po proudu = místní z, UV.y = 1 − hloubka),
## bílou barvu vrcholů (kraj, bez pěny) a materiál hlavni.mat_voda s parametry pro mělkou čistou vodu.
func _voda_studanky(k: Node3D) -> void:
	var vo: Dictionary = Pravidla.cti("zajimava_mista", "funkce", "studanka").get("voda", {})
	var mv = hlavni.get("mat_voda")
	if vo.is_empty() or not (mv is ShaderMaterial): return
	var m2 := (mv as ShaderMaterial).duplicate() as ShaderMaterial
	for kk: String in vo["shader"]: m2.set_shader_parameter(kk, float(vo["shader"][kk]))
	for mi in k.find_children("*", "MeshInstance3D", true, false):
		var am := (mi as MeshInstance3D).mesh as ArrayMesh
		if am == null: continue
		for i in am.get_surface_count():
			var mt := am.surface_get_material(i)
			if mt == null or String(mt.resource_name) != String(vo["material"]): continue
			var arr := am.surface_get_arrays(i)
			var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uv := PackedVector2Array(); var co := PackedColorArray()
			for p in v:   # šachta hluboká, potůček (vrcholy pod potucek_pod_y) mělký
				var hl := float(vo["potucek_hloubka_m"]) if p.y < float(vo["potucek_pod_y"]) else float(vo["hloubka_m"])
				uv.append(Vector2(p.z, 1.0 - hl)); co.append(Color(1, 1, 1, 1))
			arr[Mesh.ARRAY_TEX_UV] = uv; arr[Mesh.ARRAY_COLOR] = co
			var nova := ArrayMesh.new()
			for j in am.get_surface_count():
				if j == i: nova.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr); nova.surface_set_material(j, m2)
				else: nova.add_surface_from_arrays(am.surface_get_primitive_type(j), am.surface_get_arrays(j)); nova.surface_set_material(j, am.surface_get_material(j))
			(mi as MeshInstance3D).mesh = nova
			(mi as MeshInstance3D).set_meta("voda_shader", true)
			break


## NAVOD_LES.md: „Barva vrcholů nese stárnutí – zapni Vertex Color → Use as Albedo“ (mech, saze, vlhko, uhelný prach)
func _barva_vrcholu(k: Node) -> void:
	for mi in k.find_children("*", "MeshInstance3D", true, false):
		var m := (mi as MeshInstance3D).mesh
		if m == null: continue
		for i in m.get_surface_count():
			var mt := m.surface_get_material(i) as StandardMaterial3D
			if mt and not mt.vertex_color_use_as_albedo and (m.surface_get_format(i) & Mesh.ARRAY_FORMAT_COLOR):
				mt.vertex_color_use_as_albedo = true


func _dosah(n: Node, do_m: float) -> void:
	for g in n.find_children("*", "GeometryInstance3D", true, false):
		(g as GeometryInstance3D).visibility_range_end = do_m
		if do_m > 60.0: (g as GeometryInstance3D).visibility_range_end_margin = 4.0


## konvexní kolize ze sítí (předměty katalogu nemají kolizi v glb)
func _kolize_konvexni(n: Node3D) -> void:
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		if (mi as MeshInstance3D).mesh: (mi as MeshInstance3D).create_convex_collision(true, true)


func _zemljanka(u: Node3D, di: Dictionary, mo: String) -> Node3D:
	var c := "res://modely/stavby_h/%s.glb" % mo
	if not ResourceLoader.exists(c): push_warning("ZAJIMAVA %s chybí" % c); return null
	var z := (load(c) as PackedScene).instantiate() as Node3D
	z.name = mo; z.transform = _xf(di); u.add_child(z)
	var zl: Dictionary = d["zemljanky_lod"]
	for g in z.find_children("*", "GeometryInstance3D", true, false):
		var gi := g as GeometryInstance3D
		if String(gi.name).ends_with("_Daleko"):
			gi.visibility_range_begin = float(zl["podrobny_do_m"]); gi.visibility_range_end = float(zl["obal_do_m"])
			var c_: Array = zl["obal_barva"]   # hrubý obal bez textury (Míša 14. 11.: z dálky ne světlé kostky – barva ztmavlé kůry)
			var mo_ := StandardMaterial3D.new(); mo_.albedo_color = Color(float(c_[0]), float(c_[1]), float(c_[2])); mo_.roughness = 1.0
			gi.material_override = mo_
		else:
			gi.visibility_range_end = float(zl["podrobny_do_m"])
			if String(gi.name).begins_with("Zemljanka_"): gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var ho: Dictionary = Pravidla.cti("zajimava_mista", "modely", "zemljanky").get("houne", {})   # vlněná houně od modeláře na rohožích (Míša 16. 11.)
	if ResourceLoader.exists(String(ho.get("model", ""))):
		for jm in ["Zemljanka_Spani_L", "Zemljanka_Spani_P"]:
			var zn := z.find_child(jm, true, false) as Node3D
			if zn == null: continue
			var h := (load(String(ho["model"])) as PackedScene).instantiate() as Node3D; h.name = "Houne_" + jm.right(1)
			zn.add_child(h)
			for g in h.find_children("*", "GeometryInstance3D", true, false):
				var gi := g as GeometryInstance3D
				if gi.visibility_range_begin > 0.0: gi.visibility_range_end = float(ho["do_m"])
				gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# textury chýší Havrana jsou zesvětlené (domy: mista.json modely.domy.jas_podrobny, hlavni.gd _ztlum) – stejný násobek
	var jas := float(zl.get("jas_podrobny", 1.0)); var cache := {}
	for mi in z.find_children("*", "MeshInstance3D", true, false):
		var nm := String(mi.name)
		if nm.ends_with("_Daleko") or nm.begins_with("Zemljanka_") or (mi as MeshInstance3D).mesh == null: continue
		for i in (mi as MeshInstance3D).mesh.get_surface_count():
			var mt := (mi as MeshInstance3D).mesh.surface_get_material(i) as BaseMaterial3D
			if mt == null: continue
			if not cache.has(mt):
				var m2 := mt.duplicate() as BaseMaterial3D; m2.albedo_color = mt.albedo_color * Color(jas, jas, jas); cache[mt] = m2
			(mi as MeshInstance3D).set_surface_override_material(i, cache[mt])
	return z


func _stola(u: Node3D, di: Dictionary) -> Node3D:
	var c := LES + "stola.glb"
	if not ResourceLoader.exists(c): push_warning("ZAJIMAVA štola chybí"); return null
	var s := (load(c) as PackedScene).instantiate() as Node3D
	s.name = "Stola"; s.transform = _xf(di); u.add_child(s)
	var sl: Dictionary = d["stola_lod"]
	for g in s.find_children("*", "GeometryInstance3D", true, false):
		var gi := g as GeometryInstance3D
		var ab := gi.get_aabb(); var zc := (gi.transform * ab.get_center()).z
		gi.visibility_range_end = float(sl["vstup_do_m"]) if zc > -3.0 else float(sl["chodba_do_m"])
	for cs in s.find_children("*", "CollisionShape3D", true, false):   # stěny chodby zevnitř i zvenku
		if (cs as CollisionShape3D).shape is ConcavePolygonShape3D: ((cs as CollisionShape3D).shape as ConcavePolygonShape3D).backface_collision = true
	for p: Array in d.get("stola_kahany", []):   # kahany (Stara_stola_1393.tscn: barva, energie, dosah)
		var l := OmniLight3D.new(); l.light_color = Color(1, 0.48, 0.16); l.light_energy = 0.45; l.omni_range = 3.2; l.omni_attenuation = 1.8
		l.shadow_enabled = false; l.distance_fade_enabled = true; l.distance_fade_begin = 30.0; l.distance_fade_length = 8.0
		l.position = Vector3(float(p[0]), float(p[1]), float(p[2])); s.add_child(l)
	return s


## víko kolize nad chodbou štoly: trojúhelníky z viditelné sítě terénu (svet._vs), líc nahoru (zespodu – z chodby – nekoliduje)
func _vika() -> void:
	var sv: Node = hlavni.get("svet")
	if sv == null: return
	for v: Dictionary in d.get("vika", []):
		var q: Array = v["poly"]
		var a := Vector2(q[0][0], q[0][1]); var b := Vector2(q[1][0], q[1][1]); var c := Vector2(q[3][0], q[3][1])
		var nu := maxi(2, int(a.distance_to(b))); var nv := maxi(2, int(a.distance_to(c)))
		var body := PackedVector3Array()
		var vb := func(i: int, j: int) -> Vector3:
			var p: Vector2 = a + (b - a) * (float(i) / nu) + (c - a) * (float(j) / nv)
			return Vector3(p.x, maxf(_vys_sit(sv, p.x, p.y), float(v.get("y_min", -1e9))), p.y)
		for i in nu:
			for j in nv:
				var p00: Vector3 = vb.call(i, j); var p10: Vector3 = vb.call(i + 1, j); var p01: Vector3 = vb.call(i, j + 1); var p11: Vector3 = vb.call(i + 1, j + 1)
				for t in [[p00, p10, p11], [p00, p11, p01]]:
					var n_: Vector3 = ((t[1] as Vector3) - (t[0] as Vector3)).cross((t[2] as Vector3) - (t[0] as Vector3))
					if n_.y > 0.0: body.append_array([t[0], t[2], t[1]])   # Godot: líc po směru hodinových ručiček
					else: body.append_array([t[0], t[1], t[2]])
		if v.get("viditelne", false):   # záplata otvoru terénu (materiál terénu), kolize ne
			var arr := []; arr.resize(Mesh.ARRAY_MAX); arr[Mesh.ARRAY_VERTEX] = body
			var nn := PackedVector3Array()
			for t_ in body.size(): nn.append(Vector3.UP)
			arr[Mesh.ARRAY_NORMAL] = nn
			var am := ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
			var mi := MeshInstance3D.new(); mi.name = "Zaplata_" + String(v["misto"]); mi.mesh = am; mi.visibility_range_end = 400.0
			mi.material_override = sv.get("mat_zem"); add_child(mi)
			continue
		var sh := ConcavePolygonShape3D.new(); sh.set_faces(body); sh.backface_collision = false
		var sb := StaticBody3D.new(); sb.name = "Viko_" + String(v["misto"]); var cs := CollisionShape3D.new(); cs.shape = sh; sb.add_child(cs); add_child(sb)


func _vys_sit(sv: Node, x: float, z: float) -> float:
	var vi: Dictionary = sv.get("vinfo")
	var w: int = vi["sirka"]; var h: int = vi["vyska"]
	var c := clampf(x - float(vi["x0_hra"]), 0.0, w - 1.001); var r := clampf(z - float(vi["z0_hra"]), 0.0, h - 1.001)
	var c0 := int(c); var r0 := int(r); var fc := c - c0; var fr := r - r0
	return lerpf(lerpf(sv._vs(r0, c0), sv._vs(r0, c0 + 1), fc), lerpf(sv._vs(r0 + 1, c0), sv._vs(r0 + 1, c0 + 1), fc), fr)


func _mlyn(u: Node3D, di: Dictionary, m: Dictionary) -> Node3D:
	var c := "res://modely/stavby_h/mlyn.glb"
	if not ResourceLoader.exists(c): push_warning("ZAJIMAVA mlýn chybí"); return null
	var ml: Dictionary = m.get("mlyn", {})
	var s := (load(c) as PackedScene).instantiate() as Node3D
	s.name = "Mlyn"; s.transform = _xf(di); u.add_child(s)
	for jm in ml.get("vynechat", []):
		var vn := s.find_child(String(jm), true, false)
		if vn: vn.get_parent().remove_child(vn); vn.free()
	var interier := s.find_child("Mlyn_Interier_skupina", true, false)
	for g in s.find_children("*", "GeometryInstance3D", true, false):
		(g as GeometryInstance3D).visibility_range_end = float(ml.get("interier_do_m", 35.0)) if interier and interier.is_ancestor_of(g) else float(ml.get("dil_do_m", 160.0))
	if ResourceLoader.exists("res://modely/stavby_h/mlyn_lod1.glb"):
		var l1 := (load("res://modely/stavby_h/mlyn_lod1.glb") as PackedScene).instantiate() as Node3D
		l1.name = "Mlyn_lod1"; l1.transform = s.transform; u.add_child(l1)
		for jm in ml.get("vynechat", []):
			var vn := l1.find_child(String(jm), true, false)
			if vn: vn.get_parent().remove_child(vn); vn.free()
		for g in l1.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).visibility_range_begin = float(ml.get("dil_do_m", 160.0)); (g as GeometryInstance3D).visibility_range_end = 900.0
		for cs in l1.find_children("*", "CollisionObject3D", true, false): cs.queue_free()
	# kolo na spodní vodu (Míša 16. 11.): spodek kola se pohybuje s proudem – kladné otočení kolem místní x posouvá spodek k −z,
	# +z místa je po proudu (smer 1) nebo proti proudu (smer −1); zastavení zdvižením kola z proudu (mlyn.zastavit)
	var smer := -float(ml.get("smer", 1.0)); var za: Dictionary = ml.get("zastavit", {})
	for jm: String in ["Mlyn_Kolo", "Mlyn_Cevnik"]:   # Havran svet.gd _mlyn_dil: kolo kolem místní x, palečník kolem y
		var k := s.find_child(jm, true, false) as Node3D
		if k == null: continue
		k.set_script(preload("res://scripts/mlyn_kolo.gd"))
		k.set("osa", Vector3.RIGHT if jm == "Mlyn_Kolo" else Vector3.UP)
		k.set("plna", smer * float(ml.get("kolo_rad_s", 0.9)) * (1.0 if jm == "Mlyn_Kolo" else float(ml.get("cevnik_nasobek", 6.0))))
		k.set("rozjezd_s", float(za.get("rozjezd_s", 4.0)))
		if jm == "Mlyn_Kolo": k.set("zdvih_m", float(za.get("zdvih_m", 0.0))); k.set("zdvih_s", float(za.get("zdvih_s", 2.0)))
		k.set("bezi", true)
		k.call("_ready"); k.set_process(true); k.add_to_group("mlyn_kolo")
	var ov: Dictionary = ml.get("ovladani", {})   # značky ovládání (funkce.gd): páka zdvihadla kola u hřídele, mletí u kamene (Havran ovladani)
	for zn: Array in [["Mlyn_Ovladani_Kolo", "paka"], ["Mlyn_Ovladani_Mleti", "mleti"]]:
		if not ov.has(zn[1]): continue
		var q: Array = ov[zn[1]]; var n3 := Node3D.new(); n3.name = zn[0]; n3.position = Vector3(float(q[0]), float(q[1]), float(q[2])); s.add_child(n3)
	return s


func _strom(u: Node3D, di: Dictionary) -> Node3D:
	var jm := String(di["strom"]); var c := "res://modely/stromy/%s.glb" % jm
	if not ResourceLoader.exists(c): return null
	var k := Node3D.new(); k.name = "Strom_" + jm; k.transform = _xf(di); u.add_child(k)
	var st := [[c, 0.0, 45.0], ["res://modely/stromy/%s_lod1.glb" % jm, 45.0, 160.0], ["res://modely/stromy/%s_daleko.glb" % jm, 160.0, 900.0]]
	for s: Array in st:
		if not ResourceLoader.exists(String(s[0])): continue
		var n := (load(String(s[0])) as PackedScene).instantiate() as Node3D; k.add_child(n)
		for g in n.find_children("*", "GeometryInstance3D", true, false):
			(g as GeometryInstance3D).visibility_range_begin = float(s[1]); (g as GeometryInstance3D).visibility_range_end = float(s[2])
	var br: Dictionary = di.get("brt", {})
	var r := float(br.get("kmen_r", 0.45))
	var sb := StaticBody3D.new(); var cs := CollisionShape3D.new(); var cy := CylinderShape3D.new(); cy.radius = r * 0.85; cy.height = 6.0
	cs.shape = cy; cs.position.y = 3.0; sb.add_child(cs); k.add_child(sb)
	if not br.is_empty() and ResourceLoader.exists(LES + "brt.glb"):
		var b := (load(LES + "brt.glb") as PackedScene).instantiate() as Node3D; b.name = "Brt"
		var a := deg_to_rad(float(br.get("smer_st", 0.0)))
		b.transform = Transform3D(Basis(Vector3.UP, a), Vector3(sin(a), 0, cos(a)) * (r - 0.02) + Vector3.UP * float(br["vyska_m"]))
		k.add_child(b); _dosah(b, 60.0)
	return k


## ---------------------------------------------------------------- efekty (Havran life._flames; NAVOD_LES.md: kouř z průduchů, žár)
func _kour(kam: Node3D, pos: Vector3, velikost: float, pocet: int, doba: float) -> CPUParticles3D:
	var p := CPUParticles3D.new(); p.amount = pocet; p.lifetime = doba; p.local_coords = false
	p.direction = Vector3.UP; p.spread = 12.0; p.initial_velocity_min = 0.25; p.initial_velocity_max = 0.55; p.gravity = Vector3(0.12, 0.08, 0.0)
	p.scale_amount_min = velikost * 0.7; p.scale_amount_max = velikost * 1.3
	var q := QuadMesh.new(); q.size = Vector2(1, 1)
	var mt := StandardMaterial3D.new(); mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mt.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES; mt.vertex_color_use_as_albedo = true
	var tex := GradientTexture2D.new(); tex.fill = GradientTexture2D.FILL_RADIAL; tex.fill_from = Vector2(0.5, 0.5); tex.fill_to = Vector2(0.5, 0.0)
	var gr := Gradient.new(); gr.set_color(0, Color(1, 1, 1, 0.55)); gr.set_color(1, Color(1, 1, 1, 0.0)); tex.gradient = gr
	mt.albedo_texture = tex; q.material = mt; p.mesh = q
	var ramp := Gradient.new(); ramp.set_color(0, Color(0.55, 0.55, 0.55, 0.0)); ramp.add_point(0.15, Color(0.6, 0.6, 0.6, 0.5)); ramp.set_color(1, Color(0.75, 0.75, 0.78, 0.0))
	p.color_ramp = ramp
	p.visibility_range_end = 300.0
	kam.add_child(p); p.global_position = pos
	return p


func _ohen(kam: Node3D, pos: Vector3) -> void:
	if hlavni.has_method("_plamen_castice"):
		var p: CPUParticles3D = hlavni._plamen_castice(0.5, 10, 0.45); p.visibility_range_end = 40.0
		kam.add_child(p); p.global_position = pos
	var l := OmniLight3D.new(); l.light_color = Color(1.0, 0.62, 0.32); l.light_energy = 1.2; l.omni_range = 5.0; l.shadow_enabled = false
	l.distance_fade_enabled = true; l.distance_fade_begin = 40.0; l.distance_fade_length = 10.0
	kam.add_child(l); l.global_position = pos + Vector3.UP * 0.4


func _milir(k: Node3D) -> void:
	var n := 0
	for z in k.find_children("Les_Milir_Kour_*", "Node3D", true, false):
		if String(z.name) == "Les_Milir_Kour_Komin" or n % 6 == 0: _kour(k, (z as Node3D).global_position, 0.9 if String(z.name).ends_with("Komin") else 0.5, 6, 6.0)
		n += 1
	var l := OmniLight3D.new(); l.light_color = Color(1.0, 0.45, 0.2); l.light_energy = 0.8; l.omni_range = 4.5; l.shadow_enabled = false
	l.distance_fade_enabled = true; l.distance_fade_begin = 60.0; l.distance_fade_length = 10.0; l.position = Vector3(0, 0.8, 0); k.add_child(l)
	for mi in k.find_children("*", "MeshInstance3D", true, false):   # žár silněji (NAVOD_LES.md: Emission 0,7 je ve dne málo)
		var m := (mi as MeshInstance3D).mesh
		if m == null: continue
		for i in m.get_surface_count():
			var mt := m.surface_get_material(i) as StandardMaterial3D
			if mt and mt.resource_name == "M_LesZar": mt.emission_energy_multiplier = 2.5


func _smolarna(k: Node3D) -> void:
	var zk := k.find_child("Les_Smolarna_Kour", true, false) as Node3D
	if zk: _kour(k, zk.global_position, 0.6, 5, 5.0)
	var oh := k.find_child("Les_Smolarna_Ohen_Dvojhrnec", true, false) as Node3D
	if oh: _ohen(k, oh.global_position)
